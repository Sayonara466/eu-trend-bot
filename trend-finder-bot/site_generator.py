"""
Category-aware multi-section website generator for Trend Finder Bot.
Generates a single self-contained index.html (CSS+JS inlined) with
THREE completely different design systems based on category:
  - stores:    Light boutique theme (Playfair Display + Inter, pastels, soft shadows)
  - crypto:    Dark Web3 theme (Space Grotesk + Inter, neon gradients, glassmorphism)
  - companies: Light corporate theme (Inter only, flat blue, structured cards)
"""

from __future__ import annotations

# ──────────────────────── Theme Configs ────────────────────────
# Each category gets its own complete visual identity.

THEMES = {
    # ═══ STORES: Light boutique / luxury ═══
    "stores": {
        "bg": "#FFFBF5",
        "bg_alt": "#F5F0EB",
        "card": "#FFFFFF",
        "text_primary": "#1A1A1A",
        "text_secondary": "#6B7280",
        "accent_start": "#C4A882",
        "accent_end": "#D4A574",
        "gradient": "linear-gradient(135deg, #C4A882 0%, #D4A574 100%)",
        "accent": "#C4A882",
        "accent_hover": "#B8976E",
        "border": "#E8E0D8",
        "border_light": "#F0EBE5",
        "footer_bg": "#1A1A1A",
        "footer_text": "#D1C7BA",
        "nav_bg": "rgba(255,251,245,0.95)",
        "nav_shadow": "rgba(0,0,0,0.05)",
        "icon": "fa-solid fa-store",
        "heading_font": "'Playfair Display', serif",
        "body_font": "'Inter', sans-serif",
        "card_shadow": "0 4px 24px rgba(0,0,0,0.06)",
        "card_shadow_hover": "0 12px 40px rgba(0,0,0,0.1)",
        "placehold_bg": "F5F0EB",
        "placehold_fg": "1A1A1A",
        "modal_bg": "rgba(255,255,255,0.95)",
        "modal_shadow": "0 20px 60px rgba(0,0,0,0.12)",
    },
    # ═══ CRYPTO: Dark Web3 / tech ═══
    "crypto": {
        "bg": "#0B0B0E",
        "bg_alt": "#0F0F13",
        "card": "#16161A",
        "text_primary": "#EAEAEA",
        "text_secondary": "#9CA3AF",
        "accent_start": "#6C5CE7",
        "accent_end": "#A29BFE",
        "gradient": "linear-gradient(135deg, #6C5CE7 0%, #A29BFE 100%)",
        "accent": "#6C5CE7",
        "accent_hover": "#5A4BD6",
        "border": "rgba(255,255,255,0.08)",
        "border_light": "rgba(255,255,255,0.06)",
        "footer_bg": "#07070A",
        "footer_text": "#9CA3AF",
        "nav_bg": "rgba(11,11,14,0.92)",
        "nav_shadow": "rgba(0,0,0,0.3)",
        "icon": "fa-solid fa-cube",
        "heading_font": "'Space Grotesk', sans-serif",
        "body_font": "'Inter', sans-serif",
        "card_shadow": "none",
        "card_shadow_hover": "0 20px 50px rgba(0,0,0,0.4)",
        "placehold_bg": "16161A",
        "placehold_fg": "9CA3AF",
        "modal_bg": "rgba(22,22,26,0.9)",
        "modal_shadow": "0 20px 60px rgba(0,0,0,0.5)",
    },
    # ═══ COMPANIES: Light corporate / B2B ═══
    "companies": {
        "bg": "#F8FAFC",
        "bg_alt": "#EFF3F8",
        "card": "#FFFFFF",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "accent_start": "#2563EB",
        "accent_end": "#2563EB",
        "gradient": "linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)",
        "accent": "#2563EB",
        "accent_hover": "#1D4ED8",
        "border": "#E2E8F0",
        "border_light": "#F1F5F9",
        "footer_bg": "#0F172A",
        "footer_text": "#94A3B8",
        "nav_bg": "rgba(248,250,252,0.95)",
        "nav_shadow": "rgba(0,0,0,0.06)",
        "icon": "fa-solid fa-rocket",
        "heading_font": "'Inter', sans-serif",
        "body_font": "'Inter', sans-serif",
        "card_shadow": "0 1px 3px rgba(0,0,0,0.08)",
        "card_shadow_hover": "0 8px 30px rgba(0,0,0,0.1)",
        "placehold_bg": "EFF3F8",
        "placehold_fg": "64748B",
        "modal_bg": "rgba(255,255,255,0.97)",
        "modal_shadow": "0 20px 60px rgba(0,0,0,0.1)",
    },
}

# ──────────────────────── Category Defaults ────────────────────────

DEFAULT_FEATURES = {
    "stores": [
        ("fa-solid fa-bag-shopping", "Curated Collections", "Handpicked designs that blend timeless elegance with modern trends"),
        ("fa-solid fa-earth-americas", "Global Shipping", "Free worldwide delivery on orders over $150 with full tracking"),
        ("fa-solid fa-leaf", "Sustainable Materials", "Ethically sourced fabrics and eco-friendly production practices"),
        ("fa-solid fa-gem", "Exclusive Pieces", "Limited edition items you won't find anywhere else"),
        ("fa-solid fa-crown", "Loyalty Rewards", "Earn points on every purchase with VIP member perks"),
        ("fa-solid fa-arrows-rotate", "Easy Returns", "30-day hassle-free returns with prepaid shipping labels"),
    ],
    "crypto": [
        ("fa-solid fa-shield-halved", "Military-Grade Security", "Multi-layer encryption with audited smart contracts and cold storage"),
        ("fa-solid fa-bolt", "Lightning Fast", "Sub-second transaction finality with zero gas fees on L2"),
        ("fa-solid fa-link", "Cross-Chain", "Seamless bridging across all major blockchain networks"),
        ("fa-solid fa-chart-line", "Real-Time Analytics", "Live dashboards with AI-powered market insights and predictions"),
        ("fa-solid fa-users", "Community Governance", "DAO-powered decision making with transparent voting"),
        ("fa-solid fa-coins", "Yield Optimization", "Auto-compounding strategies that maximize your returns"),
    ],
    "companies": [
        ("fa-solid fa-arrow-up-right-dots", "Scalable Platform", "Enterprise-grade infrastructure that grows with your business"),
        ("fa-solid fa-microchip", "AI-Powered", "Machine learning algorithms that automate and optimize workflows"),
        ("fa-solid fa-lock", "Bank-Level Security", "SOC 2 Type II certified with end-to-end encryption"),
        ("fa-solid fa-globe", "Global CDN", "99.99% uptime with edge computing across 40+ regions"),
        ("fa-solid fa-plug", "Seamless Integration", "500+ pre-built connectors for your favorite tools"),
        ("fa-solid fa-chart-pie", "Advanced Analytics", "Real-time dashboards with custom reporting and insights"),
    ],
}

DEFAULT_FAQS = {
    "stores": [
        ("What makes {name} different?", "We combine artisanal craftsmanship with modern design, creating pieces that are both timeless and contemporary. Every item tells a story of quality and sustainability."),
        ("Do you ship internationally?", "Yes! We offer free worldwide shipping on orders over $150. Standard delivery takes 5-7 business days, with express options available."),
        ("What is your return policy?", "We offer a 30-day hassle-free return policy. Items must be unworn with tags attached. We provide prepaid return shipping labels."),
        ("Are your materials sustainable?", "Absolutely. We use ethically sourced, eco-friendly materials whenever possible. Our supply chain is fully transparent and audited annually."),
        ("How can I track my order?", "Once your order ships, you'll receive a tracking number via email. You can also track it in real-time through your account dashboard."),
    ],
    "crypto": [
        ("What blockchain is {name} built on?", "We're built on a multi-chain architecture supporting Ethereum, Solana, and our own proprietary Layer 2 for maximum scalability and minimal fees."),
        ("Is {name} safe to use?", "Security is our top priority. Our smart contracts are audited by top firms, we use multi-sig wallets, and maintain full reserve transparency."),
        ("What are the fees?", "We offer zero-fee transactions on our L2 network. Mainnet operations carry minimal gas fees optimized through our batching system."),
        ("How do I get started?", "Simply connect your wallet, fund your account, and you're ready to go. Our onboarding wizard guides you through the entire process in under 2 minutes."),
        ("Do you support staking?", "Yes! Our auto-compounding staking pools offer competitive APYs with flexible lock periods. You can unstake anytime with no penalties."),
    ],
    "companies": [
        ("What industries does {name} serve?", "We serve startups, SMBs, and enterprise clients across tech, finance, healthcare, e-commerce, and SaaS industries."),
        ("Is there a free trial?", "Yes! We offer a 14-day free trial with full access to all features. No credit card required."),
        ("How secure is my data?", "We're SOC 2 Type II certified with end-to-end encryption, role-based access control, and regular third-party penetration testing."),
        ("Can I integrate with existing tools?", "Absolutely. We offer 500+ pre-built integrations with popular tools like Slack, Jira, Salesforce, HubSpot, and more."),
        ("What kind of support do you offer?", "We provide 24/7 support via chat, email, and phone. Enterprise plans include a dedicated account manager."),
    ],
}

DEFAULT_STEPS = {
    "stores": [
        ("Browse", "Explore our curated collections and discover your perfect style"),
        ("Select", "Choose your favorites and add them to your bag"),
        ("Checkout", "Secure payment with multiple options"),
        ("Receive", "Track your order in real-time and enjoy your new pieces"),
    ],
    "crypto": [
        ("Connect", "Link your wallet in seconds with our secure connection flow"),
        ("Fund", "Deposit crypto or fiat through our integrated payment system"),
        ("Trade", "Execute trades with our intuitive interface and advanced tools"),
        ("Earn", "Put your assets to work with staking and yield farming"),
    ],
    "companies": [
        ("Sign Up", "Create your account in under 60 seconds with just your email"),
        ("Configure", "Set up your workspace with our guided onboarding wizard"),
        ("Integrate", "Connect your existing tools with one-click integrations"),
        ("Launch", "Go live and start seeing results from day one"),
    ],
}

DEFAULT_STATS = {
    "stores": [("10K+", "Happy Customers"), ("50+", "Countries"), ("4.9", "Avg Rating"), ("200+", "Collections")],
    "crypto": [("500M+", "Total Volume"), ("150K+", "Active Users"), ("99.9%", "Uptime"), ("<0.5s", "Finality")],
    "companies": [("500M+", "Users Served"), ("99.9%", "Uptime SLA"), ("150+", "Integrations"), ("24/7", "Support")],
}

SEO_KEYWORDS = {
    "stores": "luxury fashion, sustainable clothing, designer brands, boutique online shopping",
    "crypto": "defi platform, crypto trading, blockchain technology, web3, decentralized finance",
    "companies": "enterprise SaaS, cloud platform, business solution, scalable infrastructure, AI-powered",
}

# ── Google Fonts URL per category ──
FONTS_URL = {
    "stores": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap",
    "crypto": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap",
    "companies": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
}


# ──────────────────────── Helpers ────────────────────────

def _s(text: str, default: str = "") -> str:
    return (text or "").strip() or default


def _first_sentence(text: str) -> str:
    for sep in (". ", ".", "\n"):
        if sep in text:
            return text.split(sep)[0].strip() + ("." if sep in (". ", ".") else "")
    return text.strip()


def _hex_to_rgb(hex_color: str) -> str:
    """Convert '#RRGGBB' to 'r,g,b' string."""
    h = hex_color.lstrip("#")
    return ",".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))


def _features(category: str, analysis: dict) -> list:
    defaults = list(DEFAULT_FEATURES[category])
    if not analysis:
        return defaults
    keywords = analysis.get("keywords", {})
    generic = keywords.get("generic", [])
    if generic:
        for i, kw in enumerate(generic[:2]):
            if i < len(defaults):
                defaults[i] = (defaults[i][0], kw.title(), defaults[i][2])
    return defaults[:6]


def _faq(category: str, name: str, analysis: dict) -> list:
    faqs = DEFAULT_FAQS[category]
    return [(q.format(name=name), a.format(name=name)) for q, a in faqs]


def _steps(category: str) -> list:
    return DEFAULT_STEPS[category]


def _stats(category: str, analysis: dict) -> list:
    return DEFAULT_STATS.get(category, DEFAULT_STATS["companies"])


def _nav_items(category: str = "companies") -> list[tuple[str, str]]:
    items = [("about", "About"), ("features", "Features"), ("killer", "Why Us"),
            ("how-it-works", "How It Works"), ("faq", "FAQ"), ("contact", "Contact")]
    if category == "stores":
        # Insert Catalog after Features
        items = [("about", "About"), ("features", "Features"), ("catalog", "Catalog"),
                ("killer", "Why Us"), ("how-it-works", "How It Works"), ("faq", "FAQ"), ("contact", "Contact")]
    return items


# ──────────────────────── CSS Generator (per category) ────────────────────────

def _generate_css(t: dict, category: str) -> str:
    rgb = _hex_to_rgb(t["accent_start"])
    tp = t["text_primary"]
    ts = t["text_secondary"]
    bg = t["bg"]
    bg_alt = t["bg_alt"]
    card = t["card"]
    border = t["border"]
    accent = t["accent"]
    hf = t["heading_font"]
    bf = t["body_font"]

    # ─── Shared base (reset + container) ───
    base = f"""*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; font-size: 16px; }}
body {{
  font-family: {bf};
  background: {bg}; color: {tp};
  line-height: 1.7; overflow-x: hidden; -webkit-font-smoothing: antialiased;
}}
a {{ color: inherit; text-decoration: none; }}
img {{ max-width: 100%; height: auto; display: block; }}
ul {{ list-style: none; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 0 24px; }}"""

    # ─── Typography ───
    typo = f"""
h1, h2, h3, h4 {{ font-family: {hf}; line-height: 1.2; font-weight: 700; }}
.section-title {{
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  text-align: center; margin-bottom: 16px; color: {tp};
}}
.section-subtitle {{
  text-align: center; color: {ts};
  max-width: 600px; margin: 0 auto 48px; font-size: 1.05rem;
}}"""

    # ─── Buttons ───
    if category == "stores":
        btn = f"""
.btn {{
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 32px; border-radius: 4px;
  font-weight: 500; font-size: 0.95rem; cursor: pointer;
  border: none; transition: all 0.3s ease;
  font-family: {bf}; letter-spacing: 0.5px; text-transform: uppercase;
}}
.btn-primary {{
  background: {tp}; color: #FFFBF5;
}}
.btn-primary:hover {{
  opacity: 0.85; transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}}
.btn-outline {{
  background: transparent; color: {tp};
  border: 1.5px solid {tp};
}}
.btn-outline:hover {{
  background: {tp}; color: #FFFBF5; transform: translateY(-2px);
}}"""
    elif category == "crypto":
        btn = f"""
.btn {{
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 32px; border-radius: 8px;
  font-weight: 600; font-size: 1rem; cursor: pointer;
  border: none; transition: all 0.3s ease;
  font-family: {bf};
}}
.btn-primary {{
  background: {t["gradient"]}; color: #0B0B0E;
}}
.btn-primary:hover {{
  opacity: 0.9; transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}}
.btn-outline {{
  background: transparent; color: {accent};
  border: 2px solid {accent};
}}
.btn-outline:hover {{
  background: {accent}; color: #0B0B0E; transform: translateY(-2px);
}}"""
    else:  # companies
        btn = f"""
.btn {{
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 32px; border-radius: 6px;
  font-weight: 600; font-size: 1rem; cursor: pointer;
  border: none; transition: all 0.3s ease;
  font-family: {bf};
}}
.btn-primary {{
  background: {accent}; color: #FFFFFF;
}}
.btn-primary:hover {{
  background: {t["accent_hover"]}; transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(37,99,235,0.25);
}}
.btn-outline {{
  background: transparent; color: {accent};
  border: 2px solid {accent};
}}
.btn-outline:hover {{
  background: {accent}; color: #FFFFFF; transform: translateY(-2px);
}}"""

    # ─── Navigation ───
    nav = f"""
.nav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  background: {t["nav_bg"]}; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid {border}; transition: all 0.3s ease;
}}
.nav-inner {{
  display: flex; align-items: center; justify-content: space-between;
  max-width: 1200px; margin: 0 auto; padding: 0 24px; height: 72px;
}}
.nav-logo {{
  font-family: {hf};
  font-size: 1.3rem; font-weight: 700; color: {tp};
  display: flex; align-items: center; gap: 8px;
}}
.nav-logo i {{ color: {accent}; font-size: 1.1rem; }}
.nav-links {{ display: flex; align-items: center; gap: 32px; }}
.nav-links a {{
  font-size: 0.9rem; font-weight: 500; color: {ts};
  transition: color 0.3s; position: relative;
}}
.nav-links a:hover {{ color: {tp}; }}
.nav-links a::after {{
  content: ''; position: absolute; bottom: -4px; left: 0;
  width: 0; height: 2px; background: {accent}; transition: width 0.3s;
}}
.nav-links a:hover::after {{ width: 100%; }}
.burger {{
  display: none; flex-direction: column; gap: 5px; cursor: pointer;
  background: none; border: none; padding: 8px;
}}
.burger span {{
  display: block; width: 24px; height: 2px; background: {tp};
  transition: all 0.3s ease; border-radius: 1px;
}}
.burger.active span:nth-child(1) {{ transform: rotate(45deg) translate(5px, 5px); }}
.burger.active span:nth-child(2) {{ opacity: 0; }}
.burger.active span:nth-child(3) {{ transform: rotate(-45deg) translate(5px, -5px); }}"""

    # ─── Hero ───
    if category == "stores":
        hero = f"""
.hero {{
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
  background: {bg};
}}
.hero-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 64px;
  align-items: center; max-width: 1200px; margin: 0 auto;
  padding: 0 24px; position: relative; z-index: 2;
}}
.hero-left {{ max-width: 560px; }}
.hero-left h1 {{
  font-size: clamp(2.2rem, 5.5vw, 3.8rem); margin-bottom: 20px;
  color: {tp}; font-weight: 600;
  line-height: 1.1; letter-spacing: -0.02em;
}}
.hero-left .hero-desc {{
  font-size: clamp(1rem, 2vw, 1.15rem);
  color: {ts}; margin-bottom: 32px; line-height: 1.8; font-weight: 300;
}}
.hero-left .hero-cta {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 48px; }}
.hero-stats {{ display: flex; gap: 40px; flex-wrap: wrap; }}
.hero-stat {{ text-align: center; }}
.hero-stat .number {{
  font-size: clamp(1.4rem, 2.5vw, 2rem); font-weight: 600;
  font-family: {hf}; color: {tp};
}}
.hero-stat .label {{ font-size: 0.8rem; color: {ts}; margin-top: 2px; }}
.hero-right {{
  display: flex; justify-content: center; align-items: center;
  perspective: 1000px;
}}
.hero-card-3d {{
  width: 100%; max-width: 480px; border-radius: 8px; overflow: hidden;
  transform: perspective(1000px) rotateY(-3deg) rotateX(1deg);
  transition: transform 0.6s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.6s ease;
  box-shadow: 0 20px 50px rgba(0,0,0,0.08);
  border: 1px solid {border};
  position: relative;
}}
.hero-card-3d:hover {{
  transform: perspective(1000px) rotateY(0deg) rotateX(0deg) translateY(-8px);
  box-shadow: 0 30px 70px rgba(0,0,0,0.12);
}}
.hero-card-3d img {{ width: 100%; height: auto; display: block; background: {bg_alt}; }}
.hero-card-3d .card-overlay {{
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 24px; background: linear-gradient(to top, rgba(255,251,245,0.95) 0%, transparent 100%);
}}
.hero-card-3d .card-overlay h3 {{ font-size: 1.1rem; color: {tp}; margin-bottom: 4px; font-family: {hf}; }}
.hero-card-3d .card-overlay p {{ font-size: 0.85rem; color: {ts}; font-weight: 300; }}"""
    elif category == "crypto":
        hero = f"""
.hero {{
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
  background: {bg};
}}
.hero-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 64px;
  align-items: center; max-width: 1200px; margin: 0 auto;
  padding: 0 24px; position: relative; z-index: 2;
}}
.hero-left {{ max-width: 560px; }}
.hero-left h1 {{
  font-size: clamp(2.2rem, 5.5vw, 3.5rem); margin-bottom: 20px;
  color: {tp}; font-weight: 800;
  line-height: 1.1;
}}
.hero-left h1 .accent-word {{
  background: {t["gradient"]}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.hero-left .hero-desc {{
  font-size: clamp(1rem, 2vw, 1.15rem);
  color: {ts}; margin-bottom: 32px; line-height: 1.7;
}}
.hero-left .hero-cta {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 48px; }}
.hero-stats {{ display: flex; gap: 40px; flex-wrap: wrap; }}
.hero-stat {{ text-align: center; }}
.hero-stat .number {{
  font-size: clamp(1.4rem, 2.5vw, 2rem); font-weight: 800;
  background: {t["gradient"]}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.hero-stat .label {{ font-size: 0.8rem; color: {ts}; margin-top: 2px; }}
.hero-right {{
  display: flex; justify-content: center; align-items: center;
  perspective: 1000px;
}}
.hero-card-3d {{
  width: 100%; max-width: 480px; border-radius: 20px; overflow: hidden;
  transform: perspective(1000px) rotateY(-5deg) rotateX(2deg);
  transition: transform 0.6s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.6s ease;
  box-shadow: 0 25px 60px rgba(0,0,0,0.5), 0 0 40px rgba({rgb},0.08);
  border: 1px solid {border};
  position: relative;
}}
.hero-card-3d:hover {{
  transform: perspective(1000px) rotateY(0deg) rotateX(0deg) translateY(-8px);
  box-shadow: 0 35px 80px rgba(0,0,0,0.6), 0 0 60px rgba({rgb},0.15);
}}
.hero-card-3d img {{ width: 100%; height: auto; display: block; background: {card}; }}
.hero-card-3d .card-overlay {{
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 24px; background: linear-gradient(to top, rgba(11,11,14,0.9) 0%, transparent 100%);
}}
.hero-card-3d .card-overlay h3 {{ font-size: 1.1rem; color: {tp}; margin-bottom: 4px; }}
.hero-card-3d .card-overlay p {{ font-size: 0.85rem; color: {ts}; }}"""
    else:  # companies
        hero = f"""
.hero {{
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
  background: {bg};
}}
.hero-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 64px;
  align-items: center; max-width: 1200px; margin: 0 auto;
  padding: 0 24px; position: relative; z-index: 2;
}}
.hero-left {{ max-width: 560px; }}
.hero-left h1 {{
  font-size: clamp(2.2rem, 5.5vw, 3.2rem); margin-bottom: 20px;
  color: {tp}; font-weight: 800;
  line-height: 1.15; letter-spacing: -0.02em;
}}
.hero-left .hero-desc {{
  font-size: clamp(1rem, 2vw, 1.1rem);
  color: {ts}; margin-bottom: 32px; line-height: 1.7;
}}
.hero-left .hero-cta {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 48px; }}
.hero-stats {{ display: flex; gap: 40px; flex-wrap: wrap; }}
.hero-stat {{ text-align: center; }}
.hero-stat .number {{
  font-size: clamp(1.4rem, 2.5vw, 2rem); font-weight: 800;
  color: {accent};
}}
.hero-stat .label {{ font-size: 0.8rem; color: {ts}; margin-top: 2px; }}
.hero-right {{
  display: flex; justify-content: center; align-items: center;
  perspective: 1000px;
}}
.hero-card-3d {{
  width: 100%; max-width: 480px; border-radius: 12px; overflow: hidden;
  transform: perspective(1000px) rotateY(-3deg) rotateX(1deg);
  transition: transform 0.6s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.6s ease;
  box-shadow: 0 12px 40px rgba(0,0,0,0.08);
  border: 1px solid {border};
  position: relative;
}}
.hero-card-3d:hover {{
  transform: perspective(1000px) rotateY(0deg) rotateX(0deg) translateY(-8px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.12);
}}
.hero-card-3d img {{ width: 100%; height: auto; display: block; background: {bg_alt}; }}
.hero-card-3d .card-overlay {{
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 24px; background: linear-gradient(to top, rgba(248,250,252,0.95) 0%, transparent 100%);
}}
.hero-card-3d .card-overlay h3 {{ font-size: 1.1rem; color: {tp}; margin-bottom: 4px; }}
.hero-card-3d .card-overlay p {{ font-size: 0.85rem; color: {ts}; }}"""

    # ─── Sections base ───
    sections = f"""
section {{ padding: 100px 0; }}
.section-dark {{ background: {bg}; }}
.section-alt {{ background: {bg_alt}; }}"""

    # ─── About ───
    about = f"""
.about-content {{
  max-width: 800px; margin: 0 auto; padding: 0 24px; text-align: center;
}}
.about-content p {{
  font-size: 1.1rem; color: {ts};
  line-height: 1.8; margin-bottom: 20px;
}}"""

    # ─── Feature cards ───
    if category == "stores":
        features = f"""
.features-grid {{
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 32px; max-width: 1200px; margin: 0 auto; padding: 0 24px;
}}
.feature-card {{
  background: {card};
  border: 1px solid {border};
  border-radius: 8px; padding: 36px;
  cursor: pointer;
  transition: transform 0.4s cubic-bezier(0.23, 1, 0.32, 1),
              box-shadow 0.4s ease;
  position: relative; overflow: hidden;
  box-shadow: {t["card_shadow"]};
}}
.feature-card:hover {{
  transform: translateY(-6px);
  box-shadow: {t["card_shadow_hover"]};
}}
.feature-card .icon-wrap {{
  width: 48px; height: 48px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: {bg_alt}; color: {accent};
  font-size: 1.1rem; margin-bottom: 20px;
}}
.feature-card h3 {{
  font-size: 1.1rem; margin-bottom: 10px; font-weight: 600;
  font-family: {hf}; color: {tp};
}}
.feature-card p {{
  color: {ts}; font-size: 0.95rem; line-height: 1.6; font-weight: 300;
}}"""
    elif category == "crypto":
        features = f"""
.features-grid {{
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 24px; max-width: 1200px; margin: 0 auto; padding: 0 24px;
}}
.feature-card {{
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  background: rgba(22,22,26,0.7);
  border: 1px solid {border};
  border-radius: 16px; padding: 32px;
  cursor: pointer;
  transition: transform 0.4s cubic-bezier(0.23, 1, 0.32, 1),
              box-shadow 0.4s ease, border-color 0.4s ease;
  position: relative; overflow: hidden;
}}
.feature-card:hover {{
  transform: translateY(-8px) rotateX(2deg);
  box-shadow: 0 20px 50px rgba(0,0,0,0.4);
  border-color: rgba(255,255,255,0.15);
}}
.feature-card .icon-wrap {{
  width: 52px; height: 52px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: {t["gradient"]}; color: #0B0B0E;
  font-size: 1.3rem; margin-bottom: 20px;
}}
.feature-card h3 {{
  font-size: 1.15rem; margin-bottom: 10px; font-weight: 700;
  font-family: {hf}; color: {tp};
}}
.feature-card p {{
  color: {ts}; font-size: 0.95rem; line-height: 1.6;
}}"""
    else:  # companies
        features = f"""
.features-grid {{
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 24px; max-width: 1200px; margin: 0 auto; padding: 0 24px;
}}
.feature-card {{
  background: {card};
  border: 1px solid {border};
  border-radius: 10px; padding: 32px;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  position: relative; overflow: hidden;
  box-shadow: {t["card_shadow"]};
}}
.feature-card:hover {{
  transform: translateY(-4px);
  box-shadow: {t["card_shadow_hover"]};
  border-color: {accent};
}}
.feature-card .icon-wrap {{
  width: 44px; height: 44px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  background: {accent}; color: #FFFFFF;
  font-size: 1.1rem; margin-bottom: 18px;
}}
.feature-card h3 {{
  font-size: 1.05rem; margin-bottom: 8px; font-weight: 700;
  font-family: {hf}; color: {tp};
}}
.feature-card p {{
  color: {ts}; font-size: 0.9rem; line-height: 1.6;
}}"""

    # ─── Killer Feature ───
    if category == "stores":
        killer = f"""
.killer {{
  padding: 100px 24px; position: relative; overflow: hidden;
  background: {bg_alt};
}}
.killer-grid {{
  display: grid; grid-template-columns: 1.2fr 1fr; gap: 64px;
  align-items: center; max-width: 1200px; margin: 0 auto;
}}
.killer-image {{
  position: relative; border-radius: 8px; overflow: hidden;
  border: 1px solid {border};
  box-shadow: 0 12px 40px rgba(0,0,0,0.06);
}}
.killer-image img {{ width: 100%; height: auto; display: block; background: {bg}; }}
.killer-image .gradient-overlay {{
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba({rgb},0.15) 0%, transparent 100%);
  pointer-events: none;
}}
.killer-text h2 {{
  font-size: clamp(1.6rem, 3.5vw, 2.4rem);
  color: {tp}; margin-bottom: 20px; font-weight: 600;
}}
.killer-text p {{
  font-size: 1.1rem; color: {ts};
  line-height: 1.8; margin-bottom: 32px; font-weight: 300;
}}"""
    elif category == "crypto":
        killer = f"""
.killer {{
  padding: 100px 24px; position: relative; overflow: hidden;
  background: {bg_alt};
}}
.killer-grid {{
  display: grid; grid-template-columns: 1.2fr 1fr; gap: 64px;
  align-items: center; max-width: 1200px; margin: 0 auto;
}}
.killer-image {{
  position: relative; border-radius: 20px; overflow: hidden;
  border: 1px solid {border};
}}
.killer-image img {{ width: 100%; height: auto; display: block; background: {card}; }}
.killer-image .gradient-overlay {{
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba({rgb},0.3) 0%, rgba(11,11,14,0.6) 100%);
  pointer-events: none;
}}
.killer-text h2 {{
  font-size: clamp(1.6rem, 3.5vw, 2.4rem);
  color: {tp}; margin-bottom: 20px;
}}
.killer-text p {{
  font-size: 1.1rem; color: {ts};
  line-height: 1.7; margin-bottom: 32px;
}}"""
    else:  # companies
        killer = f"""
.killer {{
  padding: 100px 24px; position: relative; overflow: hidden;
  background: {bg_alt};
}}
.killer-grid {{
  display: grid; grid-template-columns: 1.2fr 1fr; gap: 64px;
  align-items: center; max-width: 1200px; margin: 0 auto;
}}
.killer-image {{
  position: relative; border-radius: 12px; overflow: hidden;
  border: 1px solid {border};
  box-shadow: 0 8px 30px rgba(0,0,0,0.06);
}}
.killer-image img {{ width: 100%; height: auto; display: block; background: {bg}; }}
.killer-image .gradient-overlay {{
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba({rgb},0.12) 0%, transparent 100%);
  pointer-events: none;
}}
.killer-text h2 {{
  font-size: clamp(1.6rem, 3.5vw, 2.4rem);
  color: {tp}; margin-bottom: 20px; font-weight: 800;
}}
.killer-text p {{
  font-size: 1.1rem; color: {ts};
  line-height: 1.7; margin-bottom: 32px;
}}"""

    # ─── Steps / How It Works ───
    if category == "stores":
        steps_css = f"""
.steps-container {{
  display: flex; flex-direction: column; align-items: center; gap: 0;
  max-width: 700px; margin: 0 auto; padding: 0 24px; position: relative;
}}
.step {{
  display: flex; align-items: flex-start; gap: 24px; width: 100%;
  position: relative; padding-bottom: 48px;
}}
.step:last-child {{ padding-bottom: 0; }}
.step::before {{
  content: ''; position: absolute; left: 23px; top: 48px;
  width: 2px; bottom: 0;
  background: {border};
}}
.step:last-child::before {{ display: none; }}
.step-number {{
  width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: {bg_alt}; color: {accent};
  font-weight: 700; font-size: 1.1rem;
  font-family: {hf};
  border: 1.5px solid {border};
}}
.step-content h3 {{
  font-family: {hf};
  font-size: 1.15rem; font-weight: 600; margin-bottom: 6px;
  color: {tp};
}}
.step-content p {{ color: {ts}; font-size: 0.95rem; font-weight: 300; }}"""
    elif category == "crypto":
        steps_css = f"""
.steps-container {{
  display: flex; flex-direction: column; align-items: center; gap: 0;
  max-width: 700px; margin: 0 auto; padding: 0 24px; position: relative;
}}
.step {{
  display: flex; align-items: flex-start; gap: 24px; width: 100%;
  position: relative; padding-bottom: 48px;
}}
.step:last-child {{ padding-bottom: 0; }}
.step::before {{
  content: ''; position: absolute; left: 23px; top: 48px;
  width: 2px; bottom: 0;
  background: rgba(255,255,255,0.08);
}}
.step:last-child::before {{ display: none; }}
.step-number {{
  width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: {t["gradient"]}; color: #0B0B0E;
  font-weight: 800; font-size: 1.1rem;
  font-family: {hf};
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
.step-content h3 {{
  font-family: {hf};
  font-size: 1.15rem; font-weight: 700; margin-bottom: 6px;
  color: {tp};
}}
.step-content p {{ color: {ts}; font-size: 0.95rem; }}"""
    else:  # companies
        steps_css = f"""
.steps-container {{
  display: flex; flex-direction: column; align-items: center; gap: 0;
  max-width: 700px; margin: 0 auto; padding: 0 24px; position: relative;
}}
.step {{
  display: flex; align-items: flex-start; gap: 24px; width: 100%;
  position: relative; padding-bottom: 48px;
}}
.step:last-child {{ padding-bottom: 0; }}
.step::before {{
  content: ''; position: absolute; left: 23px; top: 48px;
  width: 2px; bottom: 0;
  background: {border};
}}
.step:last-child::before {{ display: none; }}
.step-number {{
  width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: {accent}; color: #FFFFFF;
  font-weight: 700; font-size: 1.1rem;
  font-family: {hf};
}}
.step-content h3 {{
  font-family: {hf};
  font-size: 1.15rem; font-weight: 700; margin-bottom: 6px;
  color: {tp};
}}
.step-content p {{ color: {ts}; font-size: 0.95rem; }}"""

    # ─── FAQ ───
    if category == "stores":
        faq_css = f"""
.faq-list {{
  max-width: 800px; margin: 0 auto; padding: 0 24px;
  display: flex; flex-direction: column; gap: 12px;
}}
.faq-item {{
  background: {card};
  border: 1px solid {border};
  border-radius: 8px; overflow: hidden;
  transition: border-color 0.3s ease;
  box-shadow: {t["card_shadow"]};
}}
.faq-item:hover {{ border-color: {accent}; }}
.faq-question {{
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; cursor: pointer; background: none; border: none;
  font-family: {hf};
  font-size: 1.05rem; font-weight: 600; color: {tp};
  text-align: left; gap: 16px;
}}
.faq-question:hover {{ color: {accent}; }}
.faq-arrow {{
  font-size: 0.8rem; transition: transform 0.3s ease; flex-shrink: 0;
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: {bg_alt};
}}
.faq-item.open .faq-arrow {{ transform: rotate(180deg); }}
.faq-answer {{
  max-height: 0; overflow: hidden;
  transition: max-height 0.4s ease, padding 0.3s ease;
}}
.faq-answer-inner {{
  padding: 0 24px 20px; color: {ts};
  font-size: 0.95rem; line-height: 1.7; font-weight: 300;
}}"""
    elif category == "crypto":
        faq_css = f"""
.faq-list {{
  max-width: 800px; margin: 0 auto; padding: 0 24px;
  display: flex; flex-direction: column; gap: 12px;
}}
.faq-item {{
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  background: rgba(22,22,26,0.7);
  border: 1px solid {border};
  border-radius: 14px; overflow: hidden;
  transition: border-color 0.3s ease;
}}
.faq-item:hover {{ border-color: rgba(255,255,255,0.12); }}
.faq-question {{
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; cursor: pointer; background: none; border: none;
  font-family: {bf};
  font-size: 1.05rem; font-weight: 600; color: {tp};
  text-align: left; gap: 16px;
}}
.faq-question:hover {{ color: {accent}; }}
.faq-arrow {{
  font-size: 0.8rem; transition: transform 0.3s ease; flex-shrink: 0;
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.05);
}}
.faq-item.open .faq-arrow {{ transform: rotate(180deg); }}
.faq-answer {{
  max-height: 0; overflow: hidden;
  transition: max-height 0.4s ease, padding 0.3s ease;
}}
.faq-answer-inner {{
  padding: 0 24px 20px; color: {ts};
  font-size: 0.95rem; line-height: 1.7;
}}"""
    else:  # companies
        faq_css = f"""
.faq-list {{
  max-width: 800px; margin: 0 auto; padding: 0 24px;
  display: flex; flex-direction: column; gap: 12px;
}}
.faq-item {{
  background: {card};
  border: 1px solid {border};
  border-radius: 8px; overflow: hidden;
  transition: border-color 0.3s ease;
  box-shadow: {t["card_shadow"]};
}}
.faq-item:hover {{ border-color: {accent}; }}
.faq-question {{
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; cursor: pointer; background: none; border: none;
  font-family: {bf};
  font-size: 1.05rem; font-weight: 600; color: {tp};
  text-align: left; gap: 16px;
}}
.faq-question:hover {{ color: {accent}; }}
.faq-arrow {{
  font-size: 0.8rem; transition: transform 0.3s ease; flex-shrink: 0;
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: {bg_alt};
}}
.faq-item.open .faq-arrow {{ transform: rotate(180deg); }}
.faq-answer {{
  max-height: 0; overflow: hidden;
  transition: max-height 0.4s ease, padding 0.3s ease;
}}
.faq-answer-inner {{
  padding: 0 24px 20px; color: {ts};
  font-size: 0.95rem; line-height: 1.7;
}}"""

    # ─── Contact ───
    if category == "stores":
        contact = f"""
.contact-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 48px;
  max-width: 900px; margin: 0 auto; padding: 0 24px; align-items: start;
}}
.contact-form {{ display: flex; flex-direction: column; gap: 16px; }}
.contact-form input,
.contact-form textarea {{
  width: 100%; padding: 14px 18px; border-radius: 4px;
  border: 1px solid {border};
  background: {card}; color: {tp}; font-size: 0.95rem;
  font-family: {bf};
  transition: border-color 0.3s, box-shadow 0.3s;
}}
.contact-form input::placeholder,
.contact-form textarea::placeholder {{ color: {ts}; font-weight: 300; }}
.contact-form input:focus,
.contact-form textarea:focus {{
  outline: none; border-color: {accent};
  box-shadow: 0 0 0 3px rgba({rgb},0.1);
}}
.contact-form textarea {{ resize: vertical; min-height: 120px; }}
.contact-info {{ display: flex; flex-direction: column; gap: 24px; }}
.contact-info h3 {{
  font-family: {hf};
  font-size: 1.3rem; font-weight: 600; color: {tp};
}}
.contact-info p {{ color: {ts}; line-height: 1.6; font-weight: 300; }}
.contact-info .info-row {{
  display: flex; align-items: center; gap: 12px;
  color: {ts}; font-size: 0.95rem;
}}
.contact-info .info-row i {{ color: {accent}; font-size: 1rem; width: 20px; text-align: center; }}
.contact-info .info-row a {{ color: {accent}; font-weight: 600; transition: opacity 0.3s; }}
.contact-info .info-row a:hover {{ opacity: 0.7; }}
.social-links {{ display: flex; gap: 12px; margin-top: 8px; }}
.social-link {{
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid {border}; font-size: 1rem;
  transition: all 0.3s; background: {card};
  color: {ts};
}}
.social-link:hover {{
  background: {tp}; color: {bg};
  border-color: transparent; transform: translateY(-2px);
}}"""
    elif category == "crypto":
        contact = f"""
.contact-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 48px;
  max-width: 900px; margin: 0 auto; padding: 0 24px; align-items: start;
}}
.contact-form {{ display: flex; flex-direction: column; gap: 16px; }}
.contact-form input,
.contact-form textarea {{
  width: 100%; padding: 14px 18px; border-radius: 10px;
  border: 1px solid {border};
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  background: rgba(22,22,26,0.7); color: {tp}; font-size: 0.95rem;
  font-family: {bf};
  transition: border-color 0.3s, box-shadow 0.3s;
}}
.contact-form input::placeholder,
.contact-form textarea::placeholder {{ color: {ts}; }}
.contact-form input:focus,
.contact-form textarea:focus {{
  outline: none; border-color: {accent};
  box-shadow: 0 0 0 3px rgba({rgb},0.15);
}}
.contact-form textarea {{ resize: vertical; min-height: 120px; }}
.contact-info {{ display: flex; flex-direction: column; gap: 24px; }}
.contact-info h3 {{
  font-family: {hf};
  font-size: 1.3rem; font-weight: 700; color: {tp};
}}
.contact-info p {{ color: {ts}; line-height: 1.6; }}
.contact-info .info-row {{
  display: flex; align-items: center; gap: 12px;
  color: {ts}; font-size: 0.95rem;
}}
.contact-info .info-row i {{ color: {accent}; font-size: 1rem; width: 20px; text-align: center; }}
.contact-info .info-row a {{ color: {accent}; font-weight: 600; transition: opacity 0.3s; }}
.contact-info .info-row a:hover {{ opacity: 0.8; }}
.social-links {{ display: flex; gap: 12px; margin-top: 8px; }}
.social-link {{
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid {border}; font-size: 1.1rem;
  transition: all 0.3s; background: rgba(22,22,26,0.7);
  color: {ts};
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}}
.social-link:hover {{
  background: {t["gradient"]}; color: #0B0B0E;
  border-color: transparent; transform: translateY(-2px);
}}"""
    else:  # companies
        contact = f"""
.contact-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 48px;
  max-width: 900px; margin: 0 auto; padding: 0 24px; align-items: start;
}}
.contact-form {{ display: flex; flex-direction: column; gap: 16px; }}
.contact-form input,
.contact-form textarea {{
  width: 100%; padding: 14px 18px; border-radius: 6px;
  border: 1px solid {border};
  background: {card}; color: {tp}; font-size: 0.95rem;
  font-family: {bf};
  transition: border-color 0.3s, box-shadow 0.3s;
}}
.contact-form input::placeholder,
.contact-form textarea::placeholder {{ color: {ts}; }}
.contact-form input:focus,
.contact-form textarea:focus {{
  outline: none; border-color: {accent};
  box-shadow: 0 0 0 3px rgba({rgb},0.1);
}}
.contact-form textarea {{ resize: vertical; min-height: 120px; }}
.contact-info {{ display: flex; flex-direction: column; gap: 24px; }}
.contact-info h3 {{
  font-family: {bf};
  font-size: 1.3rem; font-weight: 700; color: {tp};
}}
.contact-info p {{ color: {ts}; line-height: 1.6; }}
.contact-info .info-row {{
  display: flex; align-items: center; gap: 12px;
  color: {ts}; font-size: 0.95rem;
}}
.contact-info .info-row i {{ color: {accent}; font-size: 1rem; width: 20px; text-align: center; }}
.contact-info .info-row a {{ color: {accent}; font-weight: 600; transition: opacity 0.3s; }}
.contact-info .info-row a:hover {{ opacity: 0.8; }}
.social-links {{ display: flex; gap: 12px; margin-top: 8px; }}
.social-link {{
  width: 44px; height: 44px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid {border}; font-size: 1rem;
  transition: all 0.3s; background: {card};
  color: {ts};
}}
.social-link:hover {{
  background: {accent}; color: #FFFFFF;
  border-color: transparent; transform: translateY(-2px);
}}"""

    # ─── Footer ───
    ft_bg = t["footer_bg"]
    ft_text = t["footer_text"]
    if category == "stores":
        footer = f"""
.footer {{
  background: {ft_bg}; color: {ft_text};
  padding: 64px 0 32px;
}}
.footer-grid {{
  display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px;
  max-width: 1200px; margin: 0 auto; padding: 0 24px 40px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}}
.footer-brand .logo {{
  font-family: {hf};
  font-size: 1.3rem; font-weight: 600; margin-bottom: 12px;
  color: #FFFFFF; display: flex; align-items: center; gap: 8px;
}}
.footer-brand .logo i {{ color: {accent}; }}
.footer-brand p {{ color: rgba(255,255,255,0.4); font-size: 0.9rem; line-height: 1.6; max-width: 280px; }}
.footer-col h4 {{
  font-family: {hf};
  font-size: 0.9rem; font-weight: 600; margin-bottom: 16px;
  color: rgba(255,255,255,0.8);
}}
.footer-col a {{
  display: block; font-size: 0.85rem; color: rgba(255,255,255,0.4);
  margin-bottom: 10px; transition: color 0.3s;
}}
.footer-col a:hover {{ color: {accent}; }}
.footer-social {{ display: flex; gap: 10px; margin-top: 16px; }}
.footer-social a {{
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.5); font-size: 0.95rem;
  transition: all 0.3s;
}}
.footer-social a:hover {{
  color: #FFFFFF; border-color: rgba(255,255,255,0.2);
  background: rgba(255,255,255,0.05);
}}
.footer-bottom {{
  max-width: 1200px; margin: 0 auto; padding: 24px 24px 0;
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px;
}}
.footer-bottom p {{ font-size: 0.8rem; color: rgba(255,255,255,0.3); }}"""
    elif category == "crypto":
        footer = f"""
.footer {{
  background: {ft_bg}; color: {ft_text};
  padding: 64px 0 32px;
}}
.footer-grid {{
  display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px;
  max-width: 1200px; margin: 0 auto; padding: 0 24px 40px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}}
.footer-brand .logo {{
  font-family: {hf};
  font-size: 1.3rem; font-weight: 700; margin-bottom: 12px;
  color: {tp}; display: flex; align-items: center; gap: 8px;
}}
.footer-brand .logo i {{ color: {accent}; }}
.footer-brand p {{ color: rgba(255,255,255,0.5); font-size: 0.9rem; line-height: 1.6; max-width: 280px; }}
.footer-col h4 {{
  font-family: {bf};
  font-size: 0.9rem; font-weight: 700; margin-bottom: 16px;
  color: rgba(255,255,255,0.85);
}}
.footer-col a {{
  display: block; font-size: 0.85rem; color: rgba(255,255,255,0.45);
  margin-bottom: 10px; transition: color 0.3s;
}}
.footer-col a:hover {{ color: {accent}; }}
.footer-social {{ display: flex; gap: 10px; margin-top: 16px; }}
.footer-social a {{
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255,255,255,0.08);
  color: {ft_text}; font-size: 0.95rem;
  transition: all 0.3s;
}}
.footer-social a:hover {{
  color: {tp}; border-color: rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.05);
}}
.footer-bottom {{
  max-width: 1200px; margin: 0 auto; padding: 24px 24px 0;
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px;
}}
.footer-bottom p {{ font-size: 0.8rem; color: rgba(255,255,255,0.35); }}"""
    else:  # companies
        footer = f"""
.footer {{
  background: {ft_bg}; color: {ft_text};
  padding: 64px 0 32px;
}}
.footer-grid {{
  display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px;
  max-width: 1200px; margin: 0 auto; padding: 0 24px 40px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}}
.footer-brand .logo {{
  font-family: {bf};
  font-size: 1.3rem; font-weight: 700; margin-bottom: 12px;
  color: #FFFFFF; display: flex; align-items: center; gap: 8px;
}}
.footer-brand .logo i {{ color: {accent}; }}
.footer-brand p {{ color: rgba(255,255,255,0.5); font-size: 0.9rem; line-height: 1.6; max-width: 280px; }}
.footer-col h4 {{
  font-family: {bf};
  font-size: 0.9rem; font-weight: 700; margin-bottom: 16px;
  color: rgba(255,255,255,0.9);
}}
.footer-col a {{
  display: block; font-size: 0.85rem; color: rgba(255,255,255,0.5);
  margin-bottom: 10px; transition: color 0.3s;
}}
.footer-col a:hover {{ color: {accent}; }}
.footer-social {{ display: flex; gap: 10px; margin-top: 16px; }}
.footer-social a {{
  width: 36px; height: 36px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.6); font-size: 0.95rem;
  transition: all 0.3s;
}}
.footer-social a:hover {{
  color: #FFFFFF; border-color: rgba(255,255,255,0.2);
  background: rgba(255,255,255,0.05);
}}
.footer-bottom {{
  max-width: 1200px; margin: 0 auto; padding: 24px 24px 0;
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px;
}}
.footer-bottom p {{ font-size: 0.8rem; color: rgba(255,255,255,0.35); }}"""

    # ─── Modal ───
    modal = f"""
.modal-overlay {{
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(0,0,0,0.5); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transition: opacity 0.3s ease;
}}
.modal-overlay.active {{ opacity: 1; pointer-events: auto; }}
.modal {{
  background: {t["modal_bg"]};
  border: 1px solid {border};
  border-radius: {"20px" if category == "crypto" else "12px"};
  padding: 48px; max-width: 420px; width: 90%; text-align: center;
  box-shadow: {t["modal_shadow"]};
  transform: scale(0.9); transition: transform 0.3s ease;
}}
.modal-overlay.active .modal {{ transform: scale(1); }}
.modal .modal-icon {{
  width: 64px; height: 64px; border-radius: 50%; margin: 0 auto 20px;
  display: flex; align-items: center; justify-content: center;
  background: {t["gradient"]}; {"color: #0B0B0E;" if category == "crypto" else f"color: #FFFFFF;"}
  font-size: 1.5rem;
}}
.modal h3 {{
  font-size: 1.5rem; margin-bottom: 12px;
  font-family: {hf}; color: {tp};
}}
.modal p {{ color: {ts}; margin-bottom: 24px; line-height: 1.6; }}
.modal .btn {{ min-width: 140px; }}"""

    # ─── Animations, mobile menu, responsive ───
    animations = f"""
.fade-up {{
  opacity: 0; transform: translateY(30px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}}
.fade-up.visible {{ opacity: 1; transform: translateY(0); }}"""

    mobile_menu = f"""
.mobile-menu {{
  position: fixed; top: 72px; left: 0; right: 0; z-index: 999;
  background: {t["nav_bg"]}; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid {border};
  transform: translateY(-100%); opacity: 0;
  transition: all 0.4s ease; pointer-events: none;
}}
.mobile-menu.active {{ transform: translateY(0); opacity: 1; pointer-events: auto; }}
.mobile-menu a {{
  display: block; padding: 16px 24px; font-size: 1rem;
  color: {ts}; border-bottom: 1px solid {border};
  transition: all 0.3s;
}}
.mobile-menu a:hover {{ color: {tp}; padding-left: 32px; }}"""

    responsive = """
@media (max-width: 1024px) {
  .hero-grid { grid-template-columns: 1fr; text-align: center; gap: 48px; }
  .hero-left { max-width: 100%; }
  .hero-left .hero-cta { justify-content: center; }
  .hero-stats { justify-content: center; }
  .hero-right { order: -1; }
  .hero-card-3d { max-width: 400px; }
  .killer-grid { grid-template-columns: 1fr; }
  .features-grid { grid-template-columns: repeat(2, 1fr); }
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .contact-grid { grid-template-columns: 1fr; }
  .hero-stats { gap: 32px; }
}
@media (max-width: 768px) {
  .nav-links { display: none; }
  .burger { display: flex; }
  .hero-left h1 { font-size: clamp(1.8rem, 8vw, 2.5rem); }
  .features-grid { grid-template-columns: 1fr; }
  .footer-grid { grid-template-columns: 1fr; gap: 24px; }
  .footer-bottom { flex-direction: column; text-align: center; }
  section { padding: 72px 0; }
  .hero-stats { gap: 24px; }
  .step { flex-direction: column; align-items: center; text-align: center; }
  .step::before { display: none; }
  .killer-grid { gap: 40px; }
}"""

    # ─── Promo block (stores only) ───
    promo_css = ""
    if category == "stores":
        promo_css = f"""
.promo {{
  padding: 80px 24px;
  background: {bg_alt};
  position: relative;
  overflow: hidden;
}}
.promo-inner {{
  max-width: 1100px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 48px; align-items: center;
}}
.promo-image {{
  position: relative; border-radius: 8px; overflow: hidden;
  border: 1px solid {border};
  box-shadow: 0 16px 48px rgba(0,0,0,0.08);
}}
.promo-image img {{
  width: 100%; height: auto; display: block;
  background: {bg}; min-height: 320px; object-fit: cover;
}}
.promo-badge {{
  position: absolute; top: 16px; left: 16px;
  background: #D4443B; color: #FFF;
  font-family: {bf}; font-size: 0.75rem; font-weight: 600;
  letter-spacing: 1px; text-transform: uppercase;
  padding: 6px 14px; border-radius: 4px;
}}
.promo-text h2 {{
  font-family: {hf}; font-size: clamp(1.6rem, 3vw, 2.2rem);
  color: {tp}; margin-bottom: 12px; font-weight: 600;
}}
.promo-text .promo-subtitle {{
  font-size: 0.95rem; color: {ts}; margin-bottom: 20px; font-weight: 300; line-height: 1.6;
}}
.promo-prices {{
  display: flex; align-items: baseline; gap: 12px; margin-bottom: 28px;
}}
.promo-old-price {{
  font-size: 1.4rem; color: {ts};
  text-decoration: line-through; font-weight: 300;
}}
.promo-new-price {{
  font-size: 2rem; color: #D4443B; font-weight: 700;
  font-family: {hf};
}}
.promo-discount {{
  display: inline-block; background: rgba(212,68,59,0.1);
  color: #D4443B; font-size: 0.8rem; font-weight: 600;
  padding: 4px 10px; border-radius: 4px; margin-left: 8px;
}}"""

    # ─── Catalog grid (stores only) ───
    catalog_css = ""
    if category == "stores":
        catalog_css = f"""
.catalog {{
  padding: 100px 24px;
  background: {bg};
}}
.catalog-grid {{
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 20px; max-width: 1200px; margin: 0 auto;
}}
.product-card {{
  background: {card};
  border: 1px solid {border};
  border-radius: 8px; overflow: hidden;
  transition: transform 0.4s cubic-bezier(0.23,1,0.32,1), box-shadow 0.4s ease;
  box-shadow: {t["card_shadow"]};
  display: flex; flex-direction: column;
}}
.product-card:hover {{
  transform: translateY(-6px);
  box-shadow: {t["card_shadow_hover"]};
}}
.product-card-img {{
  position: relative;
  background: {bg_alt};
  display: flex; align-items: center; justify-content: center;
}}
.product-card-img img {{
  width: 100%; height: auto; max-height: 320px; object-fit: contain;
  display: block; transition: transform 0.5s ease;
}}
.product-card:hover .product-card-img img {{
  transform: scale(1.03);
}}
.product-card-body {{
  padding: 14px 16px; flex: 1;
  display: flex; flex-direction: column;
}}
.product-card-name {{
  font-family: {hf}; font-size: 0.9rem; font-weight: 600;
  color: {tp}; margin-bottom: 6px; line-height: 1.3;
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}}
.product-card-price {{
  font-size: 1rem; font-weight: 600;
  color: {tp}; margin-top: auto; margin-bottom: 12px;
}}
.btn-cart {{
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  width: 100%; padding: 10px 16px; border-radius: 4px;
  font-weight: 500; font-size: 0.8rem; cursor: pointer;
  border: 1.5px solid {tp}; background: transparent;
  color: {tp}; transition: all 0.3s ease;
  font-family: {bf}; letter-spacing: 0.5px; text-transform: uppercase;
}}
.btn-cart:hover {{
  background: {tp}; color: #FFFBF5; transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}}"""

    # ─── Cart modal (stores only) ───
    cart_modal_css = ""
    if category == "stores":
        cart_modal_css = f"""
.cart-modal-content {{
  text-align: center;
}}
.cart-modal-content .modal-icon {{
  background: {t["gradient"]}; color: #FFFFFF;
}}
.cart-modal-content .cart-product-name {{
  font-family: {hf}; font-size: 1.1rem; color: {tp};
  margin-bottom: 4px; font-weight: 600;
}}
.cart-modal-content .cart-modal-text {{
  color: {ts}; font-size: 0.95rem; margin-bottom: 24px; line-height: 1.5;
}}"""

    # ─── Responsive additions for promo + catalog ───
    promo_resp = ""
    if category == "stores":
        promo_resp = """
@media (max-width: 1024px) {
  .promo-inner { grid-template-columns: 1fr; text-align: center; }
  .promo-prices { justify-content: center; }
  .catalog-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .catalog-grid { grid-template-columns: repeat(2, 1fr); }
  .promo-image img { min-height: 240px; }
  .product-card-img img { max-height: 260px; }
}
@media (max-width: 480px) {
  .catalog-grid { grid-template-columns: 1fr; }
  .product-card-img img { max-height: 280px; }
}"""

    return (base + typo + btn + nav + hero + sections + about + features
            + killer + steps_css + faq_css + contact + footer + modal
            + animations + mobile_menu + promo_css + catalog_css + cart_modal_css + promo_resp + responsive)


# ──────────────────────── JS Generator ────────────────────────

def _generate_js(t: dict, category: str) -> str:
    shadow_color = "0 2px 20px rgba(0,0,0,0.3)" if category == "crypto" else "0 2px 20px rgba(0,0,0,0.06)"
    return f"""// ═══════════ Smooth Scroll ═══════════
document.querySelectorAll('a[href^="#"]').forEach(function(a) {{
  a.addEventListener('click', function(e) {{
    e.preventDefault();
    var target = document.querySelector(this.getAttribute('href'));
    if (target) {{
      target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      closeMobileMenu();
    }}
  }});
}});

// ═══════════ Burger Menu ═══════════
var burger = document.querySelector('.burger');
var mobileMenu = document.querySelector('.mobile-menu');

burger.addEventListener('click', function() {{
  this.classList.toggle('active');
  mobileMenu.classList.toggle('active');
}});

function closeMobileMenu() {{
  if (burger) burger.classList.remove('active');
  if (mobileMenu) mobileMenu.classList.remove('active');
}}

// ═══════════ FAQ Accordion ═══════════
document.querySelectorAll('.faq-question').forEach(function(btn) {{
  btn.addEventListener('click', function() {{
    var item = this.closest('.faq-item');
    var answer = item.querySelector('.faq-answer');
    var inner = answer.querySelector('.faq-answer-inner');
    var isOpen = item.classList.contains('open');

    document.querySelectorAll('.faq-item.open').forEach(function(openItem) {{
      openItem.classList.remove('open');
      openItem.querySelector('.faq-answer').style.maxHeight = '0';
    }});

    if (!isOpen) {{
      item.classList.add('open');
      answer.style.maxHeight = inner.scrollHeight + 20 + 'px';
    }}
  }});
}});

// ═══════════ Modal ═══════════
var overlay = document.getElementById('modal-overlay');

function openModal() {{
  if (overlay) {{
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }}
}}

function closeModal() {{
  if (overlay) {{
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }}
}}

if (overlay) {{
  overlay.addEventListener('click', function(e) {{
    if (e.target === overlay) closeModal();
  }});
}}

document.addEventListener('keydown', function(e) {{
  if (e.key === 'Escape') closeModal();
}});

// ═══════════ Contact Form Submit ═══════════
var contactForm = document.getElementById('contact-form');
if (contactForm) {{
  contactForm.addEventListener('submit', function(e) {{
    e.preventDefault();
    openModal();
    this.reset();
  }});
}}

// ═══════════ CTA Scroll ═══════════
document.querySelectorAll('[data-scroll]').forEach(function(el) {{
  el.addEventListener('click', function() {{
    var target = document.getElementById(this.getAttribute('data-scroll'));
    if (target) target.scrollIntoView({{ behavior: 'smooth' }});
  }});
}});

// ═══════════ Feature Cards Click ═══════════
document.querySelectorAll('.feature-card').forEach(function(card) {{
  card.addEventListener('click', function() {{
    openModal();
  }});
}});

// ═══════════ Scroll Animations (Intersection Observer) ═══════════
var observer = new IntersectionObserver(function(entries) {{
  entries.forEach(function(entry) {{
    if (entry.isIntersecting) {{
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }}
  }});
}}, {{ threshold: 0.1, rootMargin: '0px 0px -50px 0px' }});

document.querySelectorAll('.fade-up').forEach(function(el) {{
  observer.observe(el);
}});

// ═══════════ Nav scroll shadow ═══════════
var nav = document.querySelector('.nav');
window.addEventListener('scroll', function() {{
  var st = window.pageYOffset;
  if (st > 100) {{
    nav.style.boxShadow = '{shadow_color}';
  }} else {{
    nav.style.boxShadow = 'none';
  }}
}}, {{ passive: true }});

// ═══════════ Open first FAQ by default ═══════════
(function() {{
  var first = document.querySelector('.faq-item');
  if (first) {{
    first.classList.add('open');
    var ans = first.querySelector('.faq-answer');
    var inner = first.querySelector('.faq-answer-inner');
    ans.style.maxHeight = inner.scrollHeight + 20 + 'px';
  }}
}})();

// ═══════════ Cart Modal (stores) ═══════════
var cartOverlay = document.getElementById('cart-modal-overlay');
var cartProductName = document.getElementById('cart-product-name');

function openCartModal(productName) {{
  if (cartOverlay) {{
    if (cartProductName && productName) {{
      cartProductName.textContent = productName;
    }}
    cartOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    setTimeout(function() {{ closeCartModal(); }}, 2500);
  }}
}}

function closeCartModal() {{
  if (cartOverlay) {{
    cartOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }}
}}

if (cartOverlay) {{
  cartOverlay.addEventListener('click', function(e) {{
    if (e.target === cartOverlay) closeCartModal();
  }});
}}

document.querySelectorAll('.btn-cart').forEach(function(btn) {{
  btn.addEventListener('click', function() {{
    var card = this.closest('.product-card');
    var name = card ? card.querySelector('.product-card-name').textContent : 'Item';
    openCartModal(name);
  }});
}});"""


# ──────────────────────── HTML Generators for Store Sections ────────────────────────

def _build_promo_html(category: str, products: list, t: dict, ph_bg: str, ph_fg: str) -> str:
    """Build the promo/sale block HTML (stores only). Empty string for other categories."""
    if category != "stores" or not products:
        return ""
    import random as _random
    p = _random.choice(products)  # Random product from THIS catalog
    img_src = p.get("image", "")
    prod_name = p.get("name", "Выбранный товар")
    price_raw = p.get("price", "")
    # Calculate discounted price (30% off)
    old_price = price_raw if price_raw else "€199.00"
    new_price = price_raw if price_raw else "€139.30"
    if price_raw:
        import re as _re
        nums = _re.findall(r"[\d.,]+", price_raw.replace(",", "."))
        if nums:
            try:
                val = float(nums[0].replace(",", ""))
                currency_sym = price_raw.strip()[0] if price_raw.strip()[0] in "€$£₽" else "€"
                discounted = val * 0.7
                new_price = f"{currency_sym}{discounted:.2f}"
            except (ValueError, IndexError):
                pass
    else:
        old_price = "€199.00"
        new_price = "€139.30"
    return f"""
  <section class="promo" id="promo">
    <div class="promo-inner">
      <div class="promo-image fade-up">
        <img src="{img_src if img_src else f'https://placehold.co/600x500/{ph_bg}/{ph_fg}?text=Sale'}" alt="{prod_name}">
        <span class="promo-badge">-30%</span>
      </div>
      <div class="promo-text fade-up">
        <h2>Акция</h2>
        <p class="promo-subtitle">{prod_name} — по эксклюзивной цене. Только сейчас.</p>
        <div class="promo-prices">
          <span class="promo-old-price">{old_price}</span>
          <span class="promo-new-price">{new_price}</span>
          <span class="promo-discount">-30%</span>
        </div>
        <button class="btn btn-primary" data-scroll="catalog">В каталог</button>
      </div>
    </div>
  </section>"""


def _build_catalog_html(category: str, products: list, t: dict, ph_bg: str, ph_fg: str) -> str:
    """Build the full product catalog HTML (stores only). Empty string for other categories."""
    if category != "stores" or not products:
        return ""
    cards_html = "\n".join(
        f"""      <div class="product-card fade-up">
        <div class="product-card-img">
          <img src="{p.get('image', f'https://placehold.co/400x400/{ph_bg}/{ph_fg}?text=Product')}" alt="{p.get('name', 'Товар')}">
        </div>
        <div class="product-card-body">
          <div class="product-card-name">{p.get('name', 'Товар')}</div>
          <div class="product-card-price">{p.get('price', '')}</div>
          <button class="btn-cart"><i class="fa-solid fa-bag-shopping"></i> В корзину</button>
        </div>
      </div>"""
        for p in products
    )
    return f"""
  <section class="catalog" id="catalog">
    <h2 class="section-title fade-up">Каталог</h2>
    <p class="section-subtitle fade-up">Откройте для себя нашу коллекцию</p>
    <div class="catalog-grid">
{cards_html}
    </div>
  </section>"""


def _build_cart_modal_html(category: str) -> str:
    """Build the cart modal HTML (stores only). Empty string for other categories."""
    if category != "stores":
        return ""
    return """
  <!-- Cart Modal -->
  <div class="modal-overlay" id="cart-modal-overlay">
    <div class="modal cart-modal-content">
      <div class="modal-icon"><i class="fa-solid fa-bag-shopping"></i></div>
      <div class="cart-product-name" id="cart-product-name">Товар</div>
      <p class="cart-modal-text">Товар добавлен в корзину!</p>
      <button class="btn btn-primary" onclick="closeCartModal()">Продолжить покупки</button>
    </div>
  </div>"""


# ──────────────────────── HTML Generator ────────────────────────

def _generate_html(t: dict, category: str, analysis: dict, site_analysis: dict,
                 css_content: str = "", js_content: str = "", products: list | None = None) -> str:
    a = analysis or {}
    name = _s(a.get("improved_name", a.get("name", "Project")))
    desc = _s(a.get("improved_description", a.get("description", "")))
    killer = _s(a.get("killer_feature", ""))
    link = _s(a.get("improved_link", a.get("link", "#")))
    audience = _s(a.get("target_audience", ""))
    subtitle = _first_sentence(desc) if desc else "Discover something extraordinary."
    features = _features(category, a)
    faqs = _faq(category, name, a)
    steps = _steps(category)
    stats = _stats(category, a)
    nav_items = _nav_items(category)
    products = products or []
    meta_desc = subtitle
    meta_kw = SEO_KEYWORDS.get(category, "")
    brand_icon = t["icon"]
    fonts_url = FONTS_URL.get(category, FONTS_URL["companies"])
    ph_bg = t["placehold_bg"]
    ph_fg = t["placehold_fg"]

    nav_links_html = "\n".join(f'        <a href="#{nid}">{label}</a>' for nid, label in nav_items)
    mobile_links_html = "\n".join(f'      <a href="#{nid}">{label}</a>' for nid, label in nav_items)

    features_html = "\n".join(
        f"""        <div class="feature-card fade-up">
          <div class="icon-wrap"><i class="{icon}"></i></div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>"""
        for icon, title, description in features
    )

    steps_html = "\n".join(
        f"""        <div class="step fade-up">
          <div class="step-number">{i + 1}</div>
          <div class="step-content">
            <h3>{title}</h3>
            <p>{description}</p>
          </div>
        </div>"""
        for i, (title, description) in enumerate(steps)
    )

    faq_html = "\n".join(
        f"""        <div class="faq-item fade-up">
          <button class="faq-question">
            <span>{q}</span>
            <span class="faq-arrow"><i class="fa-solid fa-chevron-down"></i></span>
          </button>
          <div class="faq-answer">
            <div class="faq-answer-inner">{ans}</div>
          </div>
        </div>"""
        for q, ans in faqs
    )

    stats_html = "\n".join(
        f"""          <div class="hero-stat">
            <div class="number">{num}</div>
            <div class="label">{lbl}</div>
          </div>"""
        for num, lbl in stats
    )

    col1_items = [("about", "About"), ("features", "Features"), ("how-it-works", "How It Works")]
    col2_items = [("killer", "Why Us"), ("faq", "FAQ"), ("contact", "Contact")]
    col3_items = [("about", "Careers"), ("#", "Blog"), ("#", "Changelog")]
    col4_items = [("#", "Privacy Policy"), ("#", "Terms of Service"), ("#", "Cookie Policy")]
    col1_html = "\n".join(f'          <a href="#{nid}">{label}</a>' for nid, label in col1_items)
    col2_html = "\n".join(f'          <a href="{nid}">{label}</a>' for nid, label in col2_items)
    col3_html = "\n".join(f'          <a href="{nid}">{label}</a>' for nid, label in col3_items)
    col4_html = "\n".join(f'          <a href="{nid}">{label}</a>' for nid, label in col4_items)

    about_text = desc if len(desc) > 60 else f"{desc} {audience}"
    about_paragraphs = ""
    if about_text:
        sentences = [s.strip() for s in about_text.replace("..", ".").split(".") if s.strip()]
        mid = len(sentences) // 2
        p1 = ". ".join(sentences[:mid]) + "." if mid > 0 else about_text
        p2 = ". ".join(sentences[mid:]) + "." if mid > 0 and mid < len(sentences) else ""
        about_paragraphs = f'      <p>{p1}</p>'
        if p2 and len(p2) > 2:
            about_paragraphs += f"\n      <p>{p2}</p>"

    domain = "example.com"
    if link and link not in ("#", ""):
        domain = link.replace("https://", "").replace("http://", "").split("/")[0]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — Premium Experience</title>
  <meta name="description" content="{meta_desc}">
  <meta name="keywords" content="{name}, {meta_kw}">
  <meta property="og:title" content="{name}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{fonts_url}" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <style>
{css_content}
  </style>
</head>
<body>

  <!-- Navigation -->
  <nav class="nav">
    <div class="nav-inner">
      <a href="#" class="nav-logo"><i class="{brand_icon}"></i> {name}</a>
      <div class="nav-links">
{nav_links_html}
      </div>
      <button class="burger" aria-label="Toggle menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </nav>
  <div class="mobile-menu">
{mobile_links_html}
  </div>

  <!-- Hero -->
  <section class="hero section-dark" id="hero">
    <div class="hero-grid">
      <div class="hero-left">
        <h1 class="fade-up">{name}</h1>
        <p class="hero-desc fade-up">{subtitle}</p>
        <div class="hero-cta fade-up">
          <button class="btn btn-primary" data-scroll="features">Explore Features</button>
          <button class="btn btn-outline" data-scroll="how-it-works">How It Works</button>
        </div>
        <div class="hero-stats fade-up">
{stats_html}
        </div>
      </div>
      <div class="hero-right fade-up">
        <div class="hero-card-3d">
          <img src="https://placehold.co/600x400/{ph_bg}/{ph_fg}?text=Project" alt="{name} preview">
          <div class="card-overlay">
            <h3>{name}</h3>
            <p>{_first_sentence(killer) if killer else subtitle}</p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Promo (stores only) -->
{_build_promo_html(category, products, t, ph_bg, ph_fg)}

  <!-- About -->
  <section id="about" class="section-alt">
    <div class="container">
      <h2 class="section-title fade-up">About {name}</h2>
      <p class="section-subtitle fade-up">Redefining what's possible</p>
{about_paragraphs}
    </div>
  </section>

  <!-- Features -->
  <section id="features" class="section-dark">
    <h2 class="section-title fade-up">Features</h2>
    <p class="section-subtitle fade-up">Everything you need, nothing you don't</p>
    <div class="features-grid">
{features_html}
    </div>
  </section>

  <!-- Catalog (stores only) -->
{_build_catalog_html(category, products, t, ph_bg, ph_fg)}

  <!-- Killer Feature -->
  <section id="killer" class="killer">
    <div class="killer-grid">
      <div class="killer-image fade-up">
        <img src="https://placehold.co/700x500/{ph_bg}/{ph_fg}?text=Feature" alt="Key feature">
        <div class="gradient-overlay"></div>
      </div>
      <div class="killer-text fade-up">
        <h2>Why Choose Us</h2>
        <p>{killer if killer else "We deliver exceptional quality and unmatched value. Our commitment to excellence sets us apart from everything else in the market."}</p>
        <button class="btn btn-primary" data-scroll="how-it-works">Get Started</button>
      </div>
    </div>
  </section>

  <!-- How It Works -->
  <section id="how-it-works" class="section-alt">
    <h2 class="section-title fade-up">How It Works</h2>
    <p class="section-subtitle fade-up">Simple steps to get started</p>
    <div class="steps-container">
{steps_html}
    </div>
  </section>

  <!-- FAQ -->
  <section id="faq" class="section-dark">
    <h2 class="section-title fade-up">Frequently Asked Questions</h2>
    <p class="section-subtitle fade-up">Got questions? We have answers</p>
    <div class="faq-list">
{faq_html}
    </div>
  </section>

  <!-- Contact -->
  <section id="contact" class="section-alt">
    <h2 class="section-title fade-up">Get In Touch</h2>
    <p class="section-subtitle fade-up">We'd love to hear from you</p>
    <div class="contact-grid">
      <form class="contact-form fade-up" id="contact-form">
        <input type="text" placeholder="Your Name" required>
        <input type="email" placeholder="Email Address" required>
        <textarea placeholder="Your Message" rows="4"></textarea>
        <button type="submit" class="btn btn-primary">Send Message</button>
      </form>
      <div class="contact-info fade-up">
        <h3>Contact Info</h3>
        <p>We're here to help with any questions about our products, services, or anything else.</p>
        <div class="info-row">
          <i class="fa-solid fa-envelope"></i>
          <span>hello@{domain}</span>
        </div>
        <div class="info-row">
          <i class="fa-solid fa-globe"></i>
          <a href="{link}" target="_blank">{domain}</a>
        </div>
        <div class="social-links">
          <a href="#" class="social-link" aria-label="Twitter"><i class="fa-brands fa-x-twitter"></i></a>
          <a href="#" class="social-link" aria-label="Instagram"><i class="fa-brands fa-instagram"></i></a>
          <a href="#" class="social-link" aria-label="LinkedIn"><i class="fa-brands fa-linkedin-in"></i></a>
        </div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="footer">
    <div class="footer-grid">
      <div class="footer-brand">
        <div class="logo"><i class="{brand_icon}"></i> {name}</div>
        <p>{_first_sentence(desc) if desc else "Building the future, one step at a time."}</p>
        <div class="footer-social">
          <a href="#" aria-label="Twitter"><i class="fa-brands fa-x-twitter"></i></a>
          <a href="#" aria-label="GitHub"><i class="fa-brands fa-github"></i></a>
          <a href="#" aria-label="LinkedIn"><i class="fa-brands fa-linkedin-in"></i></a>
        </div>
      </div>
      <div class="footer-col">
        <h4>Product</h4>
{col1_html}
      </div>
      <div class="footer-col">
        <h4>Company</h4>
{col2_html}
      </div>
      <div class="footer-col">
        <h4>Legal</h4>
{col4_html}
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2025 {name}. All rights reserved.</p>
      <p>Built with passion.</p>
    </div>
  </footer>

  <!-- Modal -->
  <div class="modal-overlay" id="modal-overlay">
    <div class="modal">
      <div class="modal-icon"><i class="fa-solid fa-check"></i></div>
      <h3>Thank You!</h3>
      <p>Your message has been received. We'll get back to you within 24 hours.</p>
      <button class="btn btn-primary" onclick="closeModal()">Close</button>
    </div>
  </div>

{_build_cart_modal_html(category)}

  <script>
{js_content}
  </script>
</body>
</html>"""

    return html


# ──────────────────────── Main API ═══════════

def generate_premium_site(
    name: str,
    description: str,
    killer_feature: str,
    analysis: dict | None = None,
    category: str = "companies",
    site_analysis: dict | None = None,
    products: list | None = None,
) -> tuple[str, str, str]:
    """Generate a premium website with category-specific design.
    Returns (html, css, js) where CSS and JS are empty (inlined in HTML)."""

    if category not in THEMES:
        category = "companies"

    t = THEMES[category]

    a = analysis or {}
    if not a.get("name"):
        a["name"] = name
    if not a.get("description"):
        a["description"] = description
    if not a.get("killer_feature"):
        a["killer_feature"] = killer_feature

    css = _generate_css(t, category)
    js = _generate_js(t, category)
    html = _generate_html(t, category, a, site_analysis or {},
                         css_content=css, js_content=js, products=products or [])

    return html, "", ""
