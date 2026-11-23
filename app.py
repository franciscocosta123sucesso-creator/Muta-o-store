import os
import sqlite3
import uuid
import requests
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "5585999999999")
DB_PATH = "mutacao_store.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price_basic REAL NOT NULL,
            price_pro REAL NOT NULL,
            delivery_info TEXT NOT NULL,
            image_url TEXT DEFAULT ''
        )
    """)

    cols = [row["name"] for row in cur.execute("PRAGMA table_info(products)").fetchall()]
    if "image_url" not in cols:
        cur.execute("ALTER TABLE products ADD COLUMN image_url TEXT DEFAULT ''")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS store_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            music_url TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        INSERT OR IGNORE INTO store_settings (id, music_url)
        VALUES (1, '')
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            payment_id TEXT PRIMARY KEY,
            product_id INTEGER NOT NULL,
            tier TEXT NOT NULL,
            buyer_email TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            notified INTEGER DEFAULT 0
        )
    """)

    count = cur.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    if count == 0:
        cur.execute("""
            INSERT INTO products (name, description, price_basic, price_pro, delivery_info, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Acesso VIP Mutação",
            "Pacote digital com acesso completo e suporte direto.",
            19.90,
            39.90,
            "Login: vip@mutacao.com | Senha: Mutacao2026",
            ""
        ))

    conn.commit()
    conn.close()


init_db()


def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception:
        pass


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MUTAÇÃO STORE</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, Arial, sans-serif; }
    body { background: #0b0e14; color: #f1f5f9; padding-bottom: 90px; }
    header {
      display: flex; justify-content: space-between; align-items: center;
      padding: 16px 18px; background: #111622; border-bottom: 1px solid #1e293b;
      position: sticky; top: 0; z-index: 20;
    }
    .logo { font-size: 1.25rem; font-weight: 800; color: #10b981; line-height: 1.1; }
    .header-actions { display: flex; flex-direction: column; gap: 6px; align-items: flex-end; }
    .btn-top {
      background: #1e293b; color: #f8fafc; border: 1px solid #334155;
      padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 0.85rem;
    }
    .container { max-width: 520px; margin: 0 auto; padding: 18px; }
    .subtitle { color: #94a3b8; font-size: 0.95rem; margin-bottom: 18px; line-height: 1.4; }
    .card {
      background: #131926; border: 1px solid #1e293b; border-radius: 14px;
      overflow: hidden; margin-bottom: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    }
    .card-media {
      width: 100%; height: 190px; background: linear-gradient(135deg, #16222f, #111827);
      display: flex; align-items: center; justify-content: center; overflow: hidden;
    }
    .card-media img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .card-media .placeholder-icon { font-size: 2.6rem; opacity: 0.85; }
    .card-body { padding: 18px; }
    .card-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 6px; color: #fff; }
    .card-desc { color: #cbd5e1; font-size: 0.92rem; margin-bottom: 14px; line-height: 1.4; }
    label { display: block; font-size: 0.85rem; color: #94a3b8; margin-bottom: 6px; }
    select, input, textarea {
      width: 100%; padding: 11px 12px; border-radius: 8px; border: 1px solid #334155;
      background: #0f141f; color: #f8fafc; font-size: 0.95rem; margin-bottom: 12px;
    }
    .price-display { font-size: 1.4rem; font-weight: 800; color: #10b981; margin: 6px 0 14px; }
    .btn-primary {
      width: 100%; padding: 13px; border: none; border-radius: 10px;
      background: #10b981; color: #052e16; font-weight: 800; font-size: 1rem; cursor: pointer;
    }
    .btn-primary:hover { background: #34d399; }
    .btn-secondary {
      padding: 8px 12px; border: 1px solid #334155; border-radius: 8px;
      background: #1e293b; color: #f8fafc; font-size: 0.85rem; cursor: pointer;
    }
    .btn-danger {
      padding: 8px 12px; border: none; border-radius: 8px;
      background: #dc2626; color: #fff; font-size: 0.85rem; cursor: pointer;
    }
    .admin-box {
      background: #131926; border: 1px solid #1e293b; border-radius: 14px;
      padding: 18px; margin-top: 24px;
    }
    .admin-box h2 { font-size: 1.2rem; margin-bottom: 14px; color: #fff; }
    .admin-box h3 { font-size: 1.05rem; margin: 18px 0 10px; color: #10b981; }
    .admin-item {
      border-top: 1px solid #1e293b; padding: 12px 0;
      display: flex; justify-content: space-between; align-items: center; gap: 10px;
    }
    .admin-item-actions { display: flex; gap: 6px; flex-shrink: 0; }
    .modal {
      display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.78);
      z-index: 50; align-items: center; justify-content: center; padding: 16px;
    }
    .modal-content {
      background: #131926; border: 1px solid #334155; border-radius: 14px;
      padding: 20px; width: 100%; max-width: 420px; text-align: center;
    }
    .modal-content img { max-width: 210px; margin: 12px auto; border-radius: 8px; background: #fff; padding: 6px; }
    .pix-code {
      background: #0b0e14; padding: 10px; border-radius: 8px; font-size: 0.8rem;
      word-break: break-all; margin: 10px 0; border: 1px solid #334155;
    }
    .whatsapp-float {
      position: fixed; right: 16px; bottom: 18px; background: #22c55e; color: #052e16;
      font-weight: 700; padding: 12px 18px; border-radius: 999px; text-decoration: none;
      box-shadow: 0 6px 18px rgba(0,0,0,0.4); z-index: 30;
    }
  </style>
</head>
<body>
  <header>
    <div class="logo">⚡ MUTAÇÃO<br>STORE</div>
    <div class="header-actions">
      <button class="btn-top" id="btn-audio" onclick="toggleAudio()">🔊 Som</button>
      <button class="btn-top" onclick="document.getElementById('admin').scrollIntoView({behavior:'smooth'})">Catálogo</button>
    </div>
  </header>

  <audio id="store-music" loop preload="none"></audio>

  <div class="container">
    <p class="subtitle">Escolha um plano, gere o Pix instantâneo e receba seu acesso automaticamente após a confirmação.</p>
    <div id="products-list"></div>

    <div id="admin" class="admin-box">
      <h2 id="form-title">Gerenciar Catálogo (Adicionar Produto)</h2>
      <input type="hidden" id="prod-id" />
      <input type="text" id="prod-name" placeholder="Nome do produto" />
      <input type="text" id="prod-image" placeholder="Link da foto do produto (opcional: https://...)" />
      <textarea id="prod-desc" rows="2" placeholder="Descrição curta do produto"></textarea>
      <input type="number" step="0.01" id="prod-basic" placeholder="Preço Plano Básico (ex: 19.90)" />
      <input type="number" step="0.01" id="prod-pro" placeholder="Preço Plano Completo (ex: 39.90)" />
      <input type="text" id="prod-delivery" placeholder="Entrega automática (ex: Login: user | Senha: 123)" />
      <div style="display:flex; gap:8px;">
        <button class="btn-primary" onclick="saveProduct()">Salvar Produto</button>
        <button class="btn-secondary" id="btn-cancel-edit" style="display:none;" onclick="resetForm()">Cancelar</button>
      </div>

      <h3>Música de Entrada da Loja</h3>
      <input type="text" id="store-music-url" placeholder="Link direto da música/áudio (.mp3, .wav, .ogg)" />
      <button class="btn-secondary" style="width:100%;" onclick="saveMusic()">Salvar Música</button>

      <div id="admin-products" style="margin-top:16px;"></div>
    </div>
  </div>

  <div id="pix-modal" class="modal">
    <div class="modal-content">
      <h3 style="margin-bottom:8px;">Pagamento via Pix</h3>
      <p id="modal-status" style="color:#94a3b8; font-size:0.9rem;">Aguardando pagamento...</p>
      <img id="qr-img" src="" alt="QR Code Pix" style="display:none;" />
      <div id="pix-copy" class="pix-code"></div>
      <button class="btn-primary" style="margin-bottom:8px;" onclick="copyPix()">Copiar Código Pix</button>
      <button class="btn-secondary" style="width:100%;" onclick="closeModal()">Fechar</button>
    </div>
  </div>

  <a class="whatsapp-float" href="https://wa.me/{{ whatsapp }}" target="_blank">💬 WhatsApp</a>

  <script>
    let products = [];
    let pollTimer = null;
    let audioCtx = null;
    let musicUrl = "";
    let musicPlaying = false;

    function playChime() {
      try {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(520, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.06, audioCtx.currentTime);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.18);
      } catch (e) {}
    }

    function toggleAudio() {
      const player = document.getElementById('store-music');
      const btn = document.getElementById('btn-audio');
      if (musicUrl && musicUrl.trim() !== "") {
        if (player.src !== musicUrl) {
          player.src = musicUrl;
        }
        if (!musicPlaying) {
          player.play().then(() => {
            musicPlaying = true;
            btn.innerText = "🔇 Pausar";
          }).catch(() => {
            playChime();
            alert("Som da loja ativado!");
          });
        } else {
          player.pause();
          musicPlaying = false;
          btn.innerText = "🔊 Som";
        }
      } else {
        playChime();
        alert("Som da loja ativado!");
      }
    }

    async function loadSettings() {
      const res = await fetch('/api/settings');
      const data = await res.json();
      musicUrl = data.music_url || "";
      document.getElementById('store-music-url').value = musicUrl;
    }

    async function saveMusic() {
      const url = document.getElementById('store-music-url').value.trim();
      await fetch('/api/settings', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({music_url: url})
      });
      musicUrl = url;
      const player = document.getElementById('store-music');
      player.pause();
      musicPlaying = false;
      document.getElementById('btn-audio').innerText = "🔊 Som";
      alert("Música da loja salva!");
    }

    async function loadProducts() {
      const res = await fetch('/api/products');
      products = await res.json();
      renderStore();
      renderAdminList();
    }

    function renderStore() {
      const container = document.getElementById('products-list');
      container.innerHTML = products.map(p => {
        const mediaHtml = p.image_url && p.image_url.trim() !== ''
          ? `<img src="${p.image_url}" alt="${p.name}" onerror="this.outerHTML='<div class=\\'placeholder-icon\\'>🛒</div>'">`
          : `<div class="placeholder-icon">🛒</div>`;
        return `
          <div class="card">
            <div class="card-media">${mediaHtml}</div>
            <div class="card-body">
              <div class="card-title">${p.name}</div>
              <div class="card-desc">${p.description}</div>
              <label>Escolha o plano:</label>
              <select id="tier-${p.id}" onchange="updatePrice(${p.id})">
                <option value="basic">Básico - R$ ${Number(p.price_basic).toFixed(2)}</option>
                <option value="pro">Completo - R$ ${Number(p.price_pro).toFixed(2)}</option>
              </select>
              <div class="price-display" id="price-${p.id}">R$ ${Number(p.price_basic).toFixed(2)}</div>
              <button class="btn-primary" onclick="buyProduct(${p.id})">Comprar com Pix</button>
            </div>
          </div>
        `;
      }).join('');
    }

    function updatePrice(id) {
      const p = products.find(x => x.id === id);
      const tier = document.getElementById(`tier-${id}`).value;
      const val = tier === 'pro' ? p.price_pro : p.price_basic;
      document.getElementById(`price-${id}`).innerText = `R$ ${Number(val).toFixed(2)}`;
    }

    function renderAdminList() {
      const box = document.getElementById('admin-products');
      box.innerHTML = products.map(p => `
        <div class="admin-item">
          <div>
            <strong>${p.name}</strong><br>
            <small style="color:#94a3b8;">Básico: R$ ${Number(p.price_basic).toFixed(2)} | Completo: R$ ${Number(p.price_pro).toFixed(2)}</small>
          </div>
          <div class="admin-item-actions">
            <button class="btn-secondary" onclick="editProduct(${p.id})">Editar</button>
            <button class="btn-danger" onclick="deleteProduct(${p.id})">Excluir</button>
          </div>
        </div>
      `).join('');
    }

    function editProduct(id) {
      const p = products.find(x => x.id === id);
      if (!p) return;
      document.getElementById('form-title').innerText = 'Editar Produto';
      document.getElementById('prod-id').value = p.id;
      document.getElementById('prod-name').value = p.name;
      document.getElementById('prod-image').value = p.image_url || '';
      document.getElementById('prod-desc').value = p.description;
      document.getElementById('prod-basic').value = p.price_basic;
      document.getElementById('prod-pro').value = p.price_pro;
      document.getElementById('prod-delivery').value = p.delivery_info;
      document.getElementById('btn-cancel-edit').style.display = 'inline-block';
      document.getElementById('admin').scrollIntoView({behavior:'smooth'});
    }

    function resetForm() {
      document.getElementById('form-title').innerText = 'Gerenciar Catálogo (Adicionar Produto)';
      document.getElementById('prod-id').value = '';
      document.getElementById('prod-name').value = '';
      document.getElementById('prod-image').value = '';
      document.getElementById('prod-desc').value = '';
      document.getElementById('prod-basic').value = '';
      document.getElementById('prod-pro').value = '';
      document.getElementById('prod-delivery').value = '';
      document.getElementById('btn-cancel-edit').style.display = 'none';
    }

    async function saveProduct() {
      const id = document.getElementById('prod-id').value;
      const payload = {
        name: document.getElementById('prod-name').value.trim(),
        image_url: document.getElementById('prod-image').value.trim(),
        description: document.getElementById('prod-desc').value.trim(),
        price_basic: parseFloat(document.getElementById('prod-basic').value),
        price_pro: parseFloat(document.getElementById('prod-pro').value),
        delivery_info: document.getElementById('prod-delivery').value.trim()
      };
      if (!payload.name || !payload.description || isNaN(payload.price_basic) || isNaN(payload.price_pro) || !payload.delivery_info) {
        alert('Preencha todos os campos obrigatórios!');
        return;
      }
      const url = id ? `/api/products/${id}` : '/api/products';
      const method = id ? 'PUT' : 'POST';
      await fetch(url, {
        method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      resetForm();
      loadProducts();
    }

    async function deleteProduct(id) {
      if (!confirm('Remover este produto?')) return;
      await fetch(`/api/products/${id}`, {method: 'DELETE'});
      loadProducts();
    }

    async function buyProduct(productId) {
      const email = prompt('Digite seu e-mail para receber o acesso:');
      if (!email) return;
      const tier = document.getElementById(`tier-${productId}`).value;
      const res = await fetch('/api/create_pix', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId, tier, email})
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || 'Erro ao gerar Pix.');
        return;
      }
      document.getElementById('pix-copy').innerText = data.qr_code || '';
      if (data.qr_code_base64) {
        const img = document.getElementById('qr-img');
        img.src = `data:image/png;base64,${data.qr_code_base64}`;
        img.style.display = 'block';
      }
      document.getElementById('modal-status').innerText = 'Aguardando pagamento...';
      document.getElementById('pix-modal').style.display = 'flex';
      startPolling(data.payment_id);
    }

    function startPolling(paymentId) {
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(async () => {
        const res = await fetch(`/api/check_payment/${paymentId}`);
        const data = await res.json();
        if (data.status === 'approved') {
          clearInterval(pollTimer);
          document.getElementById('modal-status').innerHTML = `<strong style="color:#10b981;">Pagamento aprovado!</strong><br>Seu acesso: ${data.delivery_info}`;
        }
      }, 4000);
    }

    function copyPix() {
      const txt = document.getElementById('pix-copy').innerText;
      navigator.clipboard.writeText(txt);
      alert('Código Pix copiado!');
    }

    function closeModal() {
      if (pollTimer) clearInterval(pollTimer);
      document.getElementById('pix-modal').style.display = 'none';
    }

    loadSettings();
    loadProducts();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, whatsapp=WHATSAPP_NUMBER)


@app.route("/api/settings", methods=["GET"])
def get_settings():
    conn = get_db()
    row = conn.execute("SELECT music_url FROM store_settings WHERE id=1").fetchone()
    conn.close()
    return jsonify({"music_url": row["music_url"] if row else ""})


@app.route("/api/settings", methods=["PUT"])
def update_settings():
    data = request.json or {}
    music_url = (data.get("music_url") or "").strip()
    conn = get_db()
    conn.execute("UPDATE store_settings SET music_url=? WHERE id=1", (music_url,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "music_url": music_url})


@app.route("/api/products", methods=["GET"])
def list_products():
    conn = get_db()
    rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json or {}
    conn = get_db()
    conn.execute(
        "INSERT INTO products (name, description, price_basic, price_pro, delivery_info, image_url) VALUES (?, ?, ?, ?, ?, ?)",
        (
            data["name"],
            data["description"],
            float
