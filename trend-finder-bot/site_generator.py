"""
Premium multi-section website generator for Trend Finder Bot.
Generates complete (html, css, js) strings for fashion/crypto/tech sites.
"""

from __future__ import annotations

# ──────────────────────── Theme Configs ────────────────────────

THEMES = {
    "stores": {
        "bg_primary": "#FAF9F7", "bg_secondary": "#F5F0EB", "bg_card": "#FFFFFF",
        "text_primary": "#2D2D2D", "text_secondary": "#6B6B6B",
        "accent": "#B8956A", "accent_hover": "#A07D55",
        "gradient": "linear-gradient(135deg, #B8956A 0%, #D4AF7A 100%)",
        "heading_font": "Playfair Display", "body_font": "Inter",
        "hero_img": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=1400&h=800&fit=crop",
        "feature_img": "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400&h=300&fit=crop",
        "card_border": "#E8E0D8", "card_shadow": "0 4px 20px rgba(0,0,0,0.06)",
        "nav_bg": "rgba(250,249,247,0.95)", "footer_bg": "#2D2D2D", "footer_text": "#FAF9F7",
        "emoji": "👗", "btn_radius": "4px", "card_radius": "12px",
    },
    "crypto": {
        "bg_primary": "#0A0B0E", "bg_secondary": "#111218", "bg_card": "#1A1B23",
        "text_primary": "#FFFFFF", "text_secondary": "#A0A0B8",
        "accent": "#00FF88", "accent_hover": "#00DD77",
        "gradient": "linear-gradient(135deg, #00FF88 0%, #7B61FF 100%)",
        "heading_font": "Space Grotesk", "body_font": "Inter",
        "hero_img": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=1400&h=800&fit=crop",
        "feature_img": "https://images.unsplash.com/photo-1642104704074-907c0698cbd9?w=400&h=300&fit=crop",
        "card_border": "#2A2B35", "card_shadow": "0 4px 20px rgba(0,255,136,0.05)",
        "nav_bg": "rgba(10,11,14,0.95)", "footer_bg": "#070810", "footer_text": "#A0A0B8",
        "emoji": "💎", "btn_radius": "8px", "card_radius": "16px",
    },
    "companies": {
        "bg_primary": "#F8FAFC", "bg_secondary": "#FFFFFF", "bg_card": "#FFFFFF",
        "text_primary": "#0F172A", "text_secondary": "#64748B",
        "accent": "#2563EB", "accent_hover": "#1D4ED8",
        "gradient": "linear-gradient(135deg, #2563EB 0%, #0F172A 100%)",
        "heading_font": "DM Serif Display", "body_font": "Inter",
        "hero_img": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1400&h=800&fit=crop",
        "feature_img": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=300&fit=crop",
        "card_border": "#E2E8F0", "card_shadow": "0 4px 20px rgba(0,0,0,0.04)",
        "nav_bg": "rgba(248,250,252,0.95)", "footer_bg": "#0F172A", "footer_text": "#CBD5E1",
        "emoji": "🚀", "btn_radius": "6px", "card_radius": "12px",
    },
}

# ──────────────────────── Category Defaults ────────────────────────

DEFAULT_FEATURES = {
    "stores": [
        ("🛍️", "Curated Collections", "Handpicked designs that blend timeless elegance with modern trends"),
        ("🌍", "Global Shipping", "Free worldwide delivery on orders over $150 with full tracking"),
        ("🌿", "Sustainable Materials", "Ethically sourced fabrics and eco-friendly production practices"),
        ("✨", "Exclusive Pieces", "Limited edition items you won't find anywhere else"),
        ("💝", "Loyalty Rewards", "Earn points on every purchase with VIP member perks"),
        ("🔄", "Easy Returns", "30-day hassle-free returns with prepaid shipping labels"),
    ],
    "crypto": [
        ("🔐", "Military-Grade Security", "Multi-layer encryption with audited smart contracts and cold storage"),
        ("⚡", "Lightning Fast", "Sub-second transaction finality with zero gas fees on L2"),
        ("🌐", "Cross-Chain", "Seamless bridging across all major blockchain networks"),
        ("📊", "Real-Time Analytics", "Live dashboards with AI-powered market insights and predictions"),
        ("👥", "Community Governance", "DAO-powered decision making with transparent voting"),
        ("💰", "Yield Optimization", "Auto-compounding strategies that maximize your returns"),
    ],
    "companies": [
        ("📈", "Scalable Platform", "Enterprise-grade infrastructure that grows with your business"),
        ("🤖", "AI-Powered", "Machine learning algorithms that automate and optimize workflows"),
        ("🔒", "Bank-Level Security", "SOC 2 Type II certified with end-to-end encryption"),
        ("🌍", "Global CDN", "99.99% uptime with edge computing across 40+ regions"),
        ("🤝", "Seamless Integration", "500+ pre-built connectors for your favorite tools"),
        ("📊", "Advanced Analytics", "Real-time dashboards with custom reporting and insights"),
    ],
}

DEFAULT_FAQS = {
    "stores": [
        ("What makes {name} different?", "We combine artisanal craftsmanship with modern design, creating pieces that are both timeless and contemporary. Every item tells a story of quality and sustainability."),
        ("Do you ship internationally?", "Yes! We offer free worldwide shipping on orders over $150. Standard delivery takes 5-7 business days, with express options available."),
        ("What is your return policy?", "We offer a 30-day hassle-free return policy. Items must be unworn with tags attached. We provide prepaid return shipping labels."),
        ("Are your materials sustainable?", "Absolutely. We use ethically sourced, eco-friendly materials whenever possible. Our supply chain is fully transparent and audited annually."),
        ("How can I track my order?", "Once your order ships, you'll receive a tracking number via email. You can also track it in real-time through your account dashboard."),
        ("Do you offer personal styling?", "Yes! Our complimentary personal styling service helps you find the perfect pieces. Book a session through our website or app."),
        ("Is there a loyalty program?", "Our VIP program rewards you with points on every purchase, early access to new collections, and exclusive member-only discounts."),
    ],
    "crypto": [
        ("What blockchain is {name} built on?", "We're built on a multi-chain architecture supporting Ethereum, Solana, and our own proprietary Layer 2 for maximum scalability and minimal fees."),
        ("Is {name} safe to use?", "Security is our top priority. Our smart contracts are audited by top firms, we use multi-sig wallets, and maintain full reserve transparency."),
        ("What are the fees?", "We offer zero-fee transactions on our L2 network. Mainnet operations carry minimal gas fees that are optimized through our batching system."),
        ("How do I get started?", "Simply connect your wallet, fund your account, and you're ready to go. Our onboarding wizard guides you through the entire process in under 2 minutes."),
        ("Do you support staking?", "Yes! Our auto-compounding staking pools offer competitive APYs with flexible lock periods. You can unstake anytime with no penalties."),
        ("Is there a mobile app?", "Our iOS and Android apps provide full functionality on the go, including push notifications for price alerts and portfolio changes."),
        ("How does governance work?", "{name} token holders can vote on protocol upgrades, fee structures, and treasury allocation through our transparent DAO governance system."),
    ],
    "companies": [
        ("What industries does {name} serve?", "We serve startups, SMBs, and enterprise clients across tech, finance, healthcare, e-commerce, and SaaS industries. Our platform adapts to any vertical."),
        ("Is there a free trial?", "Yes! We offer a 14-day free trial with full access to all features. No credit card required to get started."),
        ("How secure is my data?", "We're SOC 2 Type II certified with end-to-end encryption, role-based access control, and regular third-party penetration testing."),
        ("Can I integrate with existing tools?", "Absolutely. We offer 500+ pre-built integrations with popular tools like Slack, Jira, Salesforce, HubSpot, and more via our open API."),
        ("What kind of support do you offer?", "We provide 24/7 support via chat, email, and phone. Enterprise plans include a dedicated account manager and custom onboarding."),
        ("Do you offer enterprise plans?", "Yes, our enterprise plan includes custom integrations, dedicated infrastructure, SLA guarantees, and priority support with a named account manager."),
        ("How do I migrate from my current provider?", "Our migration team handles the entire process for you, including data transfer, configuration, and training — at no extra cost."),
    ],
}

DEFAULT_STEPS = {
    "stores": [
        ("Browse", "Explore our curated collections and discover your perfect style"),
        ("Select", "Choose your favorites and add them to your bag"),
        ("Checkout", "Secure payment with multiple options including crypto"),
        ("Receive", "Track your order in real-time and enjoy your new pieces"),
    ],
    "crypto": [
        ("Connect", "Link your wallet in seconds with our secure connection flow"),
        ("Fund", "Deposit crypto or fiat through our integrated payment system"),
        ("Trade", "Execute trades with our intuitive interface and advanced tools"),
        ("Earn", "Put your assets to work with staking and yield farming"),
        ("Track", "Monitor your portfolio with real-time analytics and alerts"),
    ],
    "companies": [
        ("Sign Up", "Create your account in under 60 seconds with just your email"),
        ("Configure", "Set up your workspace with our guided onboarding wizard"),
        ("Integrate", "Connect your existing tools with one-click integrations"),
        ("Launch", "Go live and start seeing results from day one"),
    ],
}

DEFAULT_STATS = {
    "stores": [("10K+", "Happy Customers"), ("50+", "Countries"), ("4.9★", "Avg Rating"), ("200+", "Collections")],
    "crypto": [("500M+", "Total Volume"), ("150K+", "Active Users"), ("99.9%", "Uptime"), ("<0.5s", "Finality")],
    "companies": [("500M+", "Users Served"), ("99.9%", "Uptime SLA"), ("150+", "Integrations"), ("24/7", "Support")],
}

SEO_KEYWORDS = {
    "stores": "luxury fashion, sustainable clothing, designer brands, boutique online shopping",
    "crypto": "defi platform, crypto trading, blockchain technology, web3, decentralized finance",
    "companies": "enterprise SaaS, cloud platform, business solution, scalable infrastructure, AI-powered",
}


# ──────────────────────── Helpers ────────────────────────

def _s(text: str, default: str = "") -> str:
    """Safe string — returns default if text is None/empty."""
    return (text or "").strip() or default


def _first_sentence(text: str) -> str:
    """Extract the first sentence from text."""
    for sep in (". ", ".", "\n"):
        if sep in text:
            return text.split(sep)[0].strip() + ("." if sep == ". " or sep == "." else "")
    return text.strip()


def _features(category: str, analysis: dict) -> list:
    """Build feature list from analysis keywords or use defaults."""
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
    """Build FAQ list with project name interpolated."""
    faqs = DEFAULT_FAQS[category]
    return [(q.format(name=name), a.format(name=name)) for q, a in faqs]


def _steps(category: str) -> list:
    return DEFAULT_STEPS[category]


def _stats(category: str, analysis: dict) -> list:
    return DEFAULT_STATS.get(category, DEFAULT_STATS["companies"])


def _nav_items() -> list[tuple[str, str]]:
    return [("about", "About"), ("features", "Features"), ("killer", "Why Us"),
            ("how-it-works", "How It Works"), ("faq", "FAQ"), ("contact", "Contact")]


# ──────────────────────── CSS Generator ────────────────────────

def _generate_css(t: dict, category: str) -> str:
    is_dark = category == "crypto"
    return f"""/* ═══════════ Reset & Base ═══════════ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; font-size: 16px; }}
body {{
  font-family: '{t["body_font"]}', sans-serif;
  background: {t["bg_primary"]}; color: {t["text_primary"]};
  line-height: 1.7; overflow-x: hidden; -webkit-font-smoothing: antialiased;
}}
a {{ color: inherit; text-decoration: none; }}
img {{ max-width: 100%; height: auto; display: block; }}
ul {{ list-style: none; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 0 24px; }}

/* ═══════════ Typography ═══════════ */
h1, h2, h3 {{ font-family: '{t["heading_font"]}', serif; line-height: 1.2; }}
.section-title {{
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  text-align: center; margin-bottom: 16px; color: {t["text_primary"]};
}}
.section-subtitle {{
  text-align: center; color: {t["text_secondary"]};
  max-width: 600px; margin: 0 auto 48px; font-size: 1.05rem;
}}

/* ═══════════ Buttons ═══════════ */
.btn {{
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 32px; border-radius: {t["btn_radius"]};
  font-weight: 600; font-size: 1rem; cursor: pointer;
  border: none; transition: all 0.3s ease; font-family: '{t["body_font"]}', sans-serif;
}}
.btn-primary {{
  background: {t["accent"]}; color: {t["text_primary"]};
}}
.btn-primary:hover {{
  background: {t["accent_hover"]}; transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}}
.btn-outline {{
  background: transparent; color: {t["accent"]};
  border: 2px solid {t["accent"]};
}}
.btn-outline:hover {{
  background: {t["accent"]}; color: {t["bg_primary"]}; transform: translateY(-2px);
}}
.btn-white {{
  background: #fff; color: {t["text_primary"]};
}}
.btn-white:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.2); }}

/* ═══════════ Navigation ═══════════ */
.nav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  background: {t["nav_bg"]}; backdrop-filter: blur(12px);
  border-bottom: 1px solid {t["card_border"]}; transition: all 0.3s ease;
}}
.nav-inner {{
  display: flex; align-items: center; justify-content: space-between;
  max-width: 1200px; margin: 0 auto; padding: 0 24px; height: 72px;
}}
.nav-logo {{
  font-family: '{t["heading_font"]}', serif;
  font-size: 1.4rem; font-weight: 700; color: {t["text_primary"]};
}}
.nav-links {{ display: flex; align-items: center; gap: 32px; }}
.nav-links a {{
  font-size: 0.9rem; font-weight: 500; color: {t["text_secondary"]};
  transition: color 0.3s; position: relative;
}}
.nav-links a:hover {{ color: {t["accent"]}; }}
.nav-links a::after {{
  content: ''; position: absolute; bottom: -4px; left: 0;
  width: 0; height: 2px; background: {t["accent"]}; transition: width 0.3s;
}}
.nav-links a:hover::after {{ width: 100%; }}
.burger {{
  display: none; flex-direction: column; gap: 5px; cursor: pointer;
  background: none; border: none; padding: 8px;
}}
.burger span {{
  display: block; width: 24px; height: 2px; background: {t["text_primary"]};
  transition: all 0.3s ease;
}}
.burger.active span:nth-child(1) {{ transform: rotate(45deg) translate(5px, 5px); }}
.burger.active span:nth-child(2) {{ opacity: 0; }}
.burger.active span:nth-child(3) {{ transform: rotate(-45deg) translate(5px, -5px); }}

/* ═══════════ Hero ═══════════ */
.hero {{
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden; text-align: center;
  background: {t["bg_primary"]};
}}
.hero-bg {{
  position: absolute; inset: 0; z-index: 0;
}}
.hero-bg img {{
  width: 100%; height: 100%; object-fit: cover;
}}
.hero-overlay {{
  position: absolute; inset: 0;
  background: {'rgba(10,11,14,0.7)' if is_dark else 'rgba(250,249,247,0.85)'};
  z-index: 1;
}}
.hero-content {{ position: relative; z-index: 2; max-width: 800px; padding: 24px; }}
.hero-content h1 {{
  font-size: clamp(2.2rem, 6vw, 4rem); margin-bottom: 20px;
  color: {'#FFFFFF' if is_dark else t["text_primary"]};
}}
.hero-content p {{
  font-size: clamp(1rem, 2.5vw, 1.25rem);
  color: {'rgba(255,255,255,0.85)' if is_dark else t["text_secondary"]};
  margin-bottom: 36px; line-height: 1.6;
}}
.hero-stats {{
  display: flex; justify-content: center; gap: 48px; margin-top: 48px; flex-wrap: wrap;
}}
.hero-stat {{
  text-align: center; color: {'#FFFFFF' if is_dark else t["text_primary"]};
}}
.hero-stat .number {{
  font-family: '{t["heading_font"]}', serif;
  font-size: clamp(1.5rem, 3vw, 2.2rem); font-weight: 700;
  color: {t["accent"]};
}}
.hero-stat .label {{ font-size: 0.85rem; color: {'rgba(255,255,255,0.7)' if is_dark else t["text_secondary"]}; }}

/* ═══════════ Sections ═══════════ */
section {{ padding: 100px 0; }}
section:nth-child(even) {{ background: {t["bg_secondary"]}; }}

/* ═══════════ Features ═══════════ */
.features-grid {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px; max-width: 1200px; margin: 0 auto; padding: 0 24px;
}}
.feature-card {{
  background: {t["bg_card"]}; border: 1px solid {t["card_border"]};
  border-radius: {t["card_radius"]}; padding: 32px;
  box-shadow: {t["card_shadow"]}; cursor: pointer;
  transition: all 0.4s ease; position: relative; overflow: hidden;
}}
.feature-card:hover {{
  transform: translateY(-6px);
  box-shadow: {'0 12px 40px rgba(0,255,136,0.12), 0 0 0 1px rgba(0,255,136,0.3)' if is_dark else '0 12px 40px rgba(0,0,0,0.1)'};
  border-color: {t["accent"]};
}}
.feature-card .icon {{
  font-size: 2.2rem; margin-bottom: 16px; display: block;
}}
.feature-card h3 {{
  font-size: 1.2rem; margin-bottom: 10px; font-family: '{t["body_font"]}', sans-serif;
  font-weight: 700;
}}
.feature-card p {{
  color: {t["text_secondary"]}; font-size: 0.95rem; line-height: 1.6;
}}

/* ═══════════ Killer Feature ═══════════ */
.killer {{
  background: {t["gradient"]}; padding: 80px 24px; text-align: center;
  position: relative; overflow: hidden;
}}
.killer::before {{
  content: ''; position: absolute; inset: 0;
  background: {'radial-gradient(circle at 20% 50%, rgba(255,255,255,0.1) 0%, transparent 50%)' if is_dark else 'radial-gradient(circle at 80% 50%, rgba(255,255,255,0.3) 0%, transparent 50%)'};
}}
.killer-inner {{ position: relative; z-index: 1; max-width: 800px; margin: 0 auto; }}
.killer .icon {{ font-size: 3.5rem; margin-bottom: 24px; display: block; }}
.killer h2 {{
  font-size: clamp(1.6rem, 4vw, 2.4rem);
  color: {'#FFFFFF' if is_dark else '#FFFFFF'}; margin-bottom: 16px;
}}
.killer p {{
  font-size: 1.15rem; color: {'rgba(255,255,255,0.9)' if is_dark else 'rgba(255,255,255,0.95)'};
  max-width: 600px; margin: 0 auto 32px;
}}

/* ═══════════ How It Works ═══════════ */
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
  background: {t["card_border"]};
}}
.step:last-child::before {{ display: none; }}
.step-number {{
  width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: {t["accent"]}; color: {'#0A0B0E' if is_dark else '#FFFFFF'};
  font-weight: 800; font-size: 1.1rem;
  font-family: '{t["body_font"]}', sans-serif;
  box-shadow: 0 4px 15px {'rgba(0,255,136,0.3)' if is_dark else 'rgba(0,0,0,0.15)'};
}}
.step-content h3 {{
  font-family: '{t["body_font"]}', sans-serif;
  font-size: 1.15rem; font-weight: 700; margin-bottom: 6px;
}}
.step-content p {{
  color: {t["text_secondary"]}; font-size: 0.95rem;
}}

/* ═══════════ FAQ ═══════════ */
.faq-list {{
  max-width: 800px; margin: 0 auto; padding: 0 24px;
  display: flex; flex-direction: column; gap: 12px;
}}
.faq-item {{
  border: 1px solid {t["card_border"]}; border-radius: {t["card_radius"]};
  overflow: hidden; background: {t["bg_card"]};
}}
.faq-question {{
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; cursor: pointer; background: none; border: none;
  font-family: '{t["body_font"]}', sans-serif;
  font-size: 1.05rem; font-weight: 600; color: {t["text_primary"]};
  text-align: left; gap: 16px;
}}
.faq-question:hover {{ color: {t["accent"]}; }}
.faq-arrow {{
  font-size: 1.2rem; transition: transform 0.3s ease; flex-shrink: 0;
}}
.faq-item.open .faq-arrow {{ transform: rotate(180deg); }}
.faq-answer {{
  max-height: 0; overflow: hidden;
  transition: max-height 0.4s ease, padding 0.3s ease;
}}
.faq-answer-inner {{
  padding: 0 24px 20px; color: {t["text_secondary"]};
  font-size: 0.95rem; line-height: 1.7;
}}

/* ═══════════ Contact ═══════════ */
.contact-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 48px;
  max-width: 900px; margin: 0 auto; padding: 0 24px; align-items: start;
}}
.contact-form {{ display: flex; flex-direction: column; gap: 16px; }}
.contact-form input,
.contact-form textarea {{
  width: 100%; padding: 14px 18px; border-radius: {t["btn_radius"]};
  border: 1px solid {t["card_border"]}; background: {t["bg_card"]};
  color: {t["text_primary"]}; font-size: 0.95rem;
  font-family: '{t["body_font"]}', sans-serif;
  transition: border-color 0.3s, box-shadow 0.3s;
}}
.contact-form input:focus,
.contact-form textarea:focus {{
  outline: none; border-color: {t["accent"]};
  box-shadow: 0 0 0 3px {'rgba(0,255,136,0.15)' if is_dark else 'rgba(184,149,106,0.15)'};
}}
.contact-form textarea {{ resize: vertical; min-height: 120px; }}
.contact-info {{ display: flex; flex-direction: column; gap: 24px; }}
.contact-info h3 {{
  font-family: '{t["body_font"]}', sans-serif;
  font-size: 1.3rem; font-weight: 700;
}}
.contact-info p {{ color: {t["text_secondary"]}; line-height: 1.6; }}
.social-links {{ display: flex; gap: 12px; margin-top: 8px; }}
.social-link {{
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid {t["card_border"]}; font-size: 1.2rem;
  transition: all 0.3s; background: {t["bg_card"]};
}}
.social-link:hover {{
  background: {t["accent"]}; color: {'#0A0B0E' if is_dark else '#FFFFFF'};
  border-color: {t["accent"]}; transform: translateY(-2px);
}}

/* ═══════════ Footer ═══════════ */
.footer {{
  background: {t["footer_bg"]}; color: {t["footer_text"]};
  padding: 64px 0 32px;
}}
.footer-grid {{
  display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px;
  max-width: 1200px; margin: 0 auto; padding: 0 24px 40px;
  border-bottom: 1px solid {'rgba(255,255,255,0.1)' if is_dark else 'rgba(255,255,255,0.08)'};
}}
.footer-brand .logo {{
  font-family: '{t["heading_font"]}', serif;
  font-size: 1.3rem; font-weight: 700; margin-bottom: 12px;
  color: {'#FFFFFF' if is_dark else '#FFFFFF'};
}}
.footer-brand p {{ color: {'rgba(255,255,255,0.6)' if is_dark else 'rgba(255,255,255,0.5)'}; font-size: 0.9rem; line-height: 1.6; max-width: 280px; }}
.footer-col h4 {{
  font-family: '{t["body_font"]}', sans-serif;
  font-size: 0.9rem; font-weight: 700; margin-bottom: 16px;
  color: {'rgba(255,255,255,0.9)' if is_dark else 'rgba(255,255,255,0.85)'};
}}
.footer-col a {{
  display: block; font-size: 0.85rem; color: {'rgba(255,255,255,0.5)' if is_dark else 'rgba(255,255,255,0.45)'};
  margin-bottom: 10px; transition: color 0.3s;
}}
.footer-col a:hover {{ color: {t["accent"]}; }}
.footer-bottom {{
  max-width: 1200px; margin: 0 auto; padding: 24px 24px 0;
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px;
}}
.footer-bottom p {{
  font-size: 0.8rem; color: {'rgba(255,255,255,0.4)' if is_dark else 'rgba(255,255,255,0.35)'};
}}

/* ═══════════ Modal ═══════════ */
.modal-overlay {{
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transition: opacity 0.3s ease;
}}
.modal-overlay.active {{ opacity: 1; pointer-events: auto; }}
.modal {{
  background: {t["bg_card"]}; border-radius: {t["card_radius"]};
  padding: 48px; max-width: 420px; width: 90%; text-align: center;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  transform: scale(0.9); transition: transform 0.3s ease;
}}
.modal-overlay.active .modal {{ transform: scale(1); }}
.modal .icon {{ font-size: 3rem; margin-bottom: 16px; display: block; }}
.modal h3 {{
  font-size: 1.5rem; margin-bottom: 12px;
  font-family: '{t["body_font"]}', sans-serif;
}}
.modal p {{ color: {t["text_secondary"]}; margin-bottom: 24px; }}
.modal .btn {{ min-width: 140px; }}

/* ═══════════ Fade Animations ═══════════ */
.fade-up {{
  opacity: 0; transform: translateY(30px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}}
.fade-up.visible {{ opacity: 1; transform: translateY(0); }}

/* ═══════════ Mobile Menu ═══════════ */
.mobile-menu {{
  position: fixed; top: 72px; left: 0; right: 0; z-index: 999;
  background: {t["nav_bg"]}; backdrop-filter: blur(12px);
  border-bottom: 1px solid {t["card_border"]};
  transform: translateY(-100%); opacity: 0;
  transition: all 0.4s ease; pointer-events: none;
}}
.mobile-menu.active {{ transform: translateY(0); opacity: 1; pointer-events: auto; }}
.mobile-menu a {{
  display: block; padding: 16px 24px; font-size: 1rem;
  color: {t["text_secondary"]}; border-bottom: 1px solid {t["card_border"]};
  transition: all 0.3s;
}}
.mobile-menu a:hover {{ color: {t["accent"]}; padding-left: 32px; }}

/* ═══════════ About ═══════════ */
.about-content {{
  max-width: 800px; margin: 0 auto; padding: 0 24px;
  text-align: center;
}}
.about-content p {{
  font-size: 1.1rem; color: {t["text_secondary"]};
  line-height: 1.8; margin-bottom: 20px;
}}

/* ═══════════ Responsive ═══════════ */
@media (max-width: 1024px) {{
  .footer-grid {{ grid-template-columns: 1fr 1fr; }}
  .contact-grid {{ grid-template-columns: 1fr; }}
  .hero-stats {{ gap: 32px; }}
}}
@media (max-width: 768px) {{
  .nav-links {{ display: none; }}
  .burger {{ display: flex; }}
  .hero-content h1 {{ font-size: clamp(1.8rem, 8vw, 2.5rem); }}
  .features-grid {{ grid-template-columns: 1fr; }}
  .footer-grid {{ grid-template-columns: 1fr; gap: 24px; }}
  .footer-bottom {{ flex-direction: column; text-align: center; }}
  section {{ padding: 72px 0; }}
  .hero-stats {{ gap: 24px; }}
  .step {{ flex-direction: column; align-items: center; text-align: center; }}
  .step::before {{ display: none; }}
}}"""


# ──────────────────────── JS Generator ────────────────────────

def _generate_js(t: dict, category: str) -> str:
    return r"""// ═══════════ Smooth Scroll ═══════════
document.querySelectorAll('a[href^="#"]').forEach(function(a) {
  a.addEventListener('click', function(e) {
    e.preventDefault();
    var target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      // Close mobile menu if open
      closeMobileMenu();
    }
  });
});

// ═══════════ Burger Menu ═══════════
var burger = document.querySelector('.burger');
var mobileMenu = document.querySelector('.mobile-menu');

burger.addEventListener('click', function() {
  this.classList.toggle('active');
  mobileMenu.classList.toggle('active');
});

function closeMobileMenu() {
  if (burger) burger.classList.remove('active');
  if (mobileMenu) mobileMenu.classList.remove('active');
}

// ═══════════ FAQ Accordion ═══════════
document.querySelectorAll('.faq-question').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var item = this.closest('.faq-item');
    var answer = item.querySelector('.faq-answer');
    var inner = answer.querySelector('.faq-answer-inner');
    var isOpen = item.classList.contains('open');

    // Close all others
    document.querySelectorAll('.faq-item.open').forEach(function(openItem) {
      openItem.classList.remove('open');
      openItem.querySelector('.faq-answer').style.maxHeight = '0';
    });

    // Toggle current
    if (!isOpen) {
      item.classList.add('open');
      answer.style.maxHeight = inner.scrollHeight + 20 + 'px';
    }
  });
});

// ═══════════ Modal ═══════════
var overlay = document.getElementById('modal-overlay');

function openModal() {
  if (overlay) {
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal() {
  if (overlay) {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }
}

if (overlay) {
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) closeModal();
  });
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeModal();
});

// ═══════════ Contact Form Submit ═══════════
var contactForm = document.getElementById('contact-form');
if (contactForm) {
  contactForm.addEventListener('submit', function(e) {
    e.preventDefault();
    openModal();
    this.reset();
  });
}

// ═══════════ CTA Scroll ═══════════
document.querySelectorAll('[data-scroll]').forEach(function(el) {
  el.addEventListener('click', function() {
    var target = document.getElementById(this.getAttribute('data-scroll'));
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  });
});

// ═══════════ Feature Cards ═══════════
document.querySelectorAll('.feature-card').forEach(function(card) {
  card.addEventListener('click', function() {
    openModal();
  });
});

// ═══════════ Scroll Animations (Intersection Observer) ═══════════
var observer = new IntersectionObserver(function(entries) {
  entries.forEach(function(entry) {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

document.querySelectorAll('.fade-up').forEach(function(el) {
  observer.observe(el);
});

// ═══════════ Nav scroll effect ═══════════
var nav = document.querySelector('.nav');
var lastScroll = 0;
window.addEventListener('scroll', function() {
  var st = window.pageYOffset;
  if (st > 100) {
    nav.style.boxShadow = '0 2px 20px rgba(0,0,0,0.08)';
  } else {
    nav.style.boxShadow = 'none';
  }
  lastScroll = st;
}, { passive: true });

// ═══════════ Open all FAQ on page load for first item ═══════════
(function() {
  var first = document.querySelector('.faq-item');
  if (first) {
    first.classList.add('open');
    var ans = first.querySelector('.faq-answer');
    var inner = first.querySelector('.faq-answer-inner');
    ans.style.maxHeight = inner.scrollHeight + 20 + 'px';
  }
})();"""


# ──────────────────────── HTML Generator ────────────────────────

def _generate_html(t: dict, category: str, analysis: dict, site_analysis: dict) -> str:
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
    nav_items = _nav_items()
    meta_desc = subtitle
    meta_kw = SEO_KEYWORDS.get(category, "")
    favicon_emoji = t["emoji"]

    # Build nav links HTML
    nav_links_html = "\n".join(f'      <a href="#{nid}">{label}</a>' for nid, label in nav_items)
    mobile_links_html = "\n".join(f'    <a href="#{nid}">{label}</a>' for nid, label in nav_items)

    # Build features HTML
    features_html = "\n".join(
        f"""      <div class="feature-card fade-up">
        <span class="icon">{icon}</span>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>"""
        for icon, title, description in features
    )

    # Build steps HTML
    steps_html = "\n".join(
        f"""      <div class="step fade-up">
        <div class="step-number">{i + 1}</div>
        <div class="step-content">
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
      </div>"""
        for i, (title, description) in enumerate(steps)
    )

    # Build FAQ HTML
    faq_html = "\n".join(
        f"""      <div class="faq-item fade-up">
        <button class="faq-question">
          <span>{q}</span>
          <span class="faq-arrow">▼</span>
        </button>
        <div class="faq-answer">
          <div class="faq-answer-inner">{ans}</div>
        </div>
      </div>"""
        for q, ans in faqs
    )

    # Build stats HTML
    stats_html = "\n".join(
        f"""        <div class="hero-stat">
          <div class="number">{num}</div>
          <div class="label">{lbl}</div>
        </div>"""
        for num, lbl in stats
    )

    # Build footer link columns
    col1_items = [("about", "About"), ("features", "Features"), ("how-it-works", "How It Works")]
    col2_items = [("killer", "Why Us"), ("faq", "FAQ"), ("contact", "Contact")]
    col1_html = "\n".join(f'      <a href="#{nid}">{label}</a>' for nid, label in col1_items)
    col2_html = "\n".join(f'      <a href="#{nid}">{label}</a>' for nid, label in col2_items)

    # About section content
    about_text = desc if len(desc) > 60 else f"{desc} {audience}"
    about_paragraphs = ""
    if about_text:
        sentences = [s.strip() for s in about_text.replace("..", ".").split(".") if s.strip()]
        mid = len(sentences) // 2
        p1 = ". ".join(sentences[:mid]) + "." if mid > 0 else about_text
        p2 = ". ".join(sentences[mid:]) + "." if mid > 0 and mid < len(sentences) else ""
        about_paragraphs = f"    <p>{p1}</p>"
        if p2 and len(p2) > 2:
            about_paragraphs += f"\n    <p>{p2}</p>"

    # Site analysis data extraction
    site_title = ""
    site_desc = ""
    if site_analysis:
        site_title = _s(site_analysis.get("title", ""))
        site_desc = _s(site_analysis.get("description", ""))

    hf = t["heading_font"]
    bf = t["body_font"]
    hf_url = hf.lower().replace(" ", "+")
    bf_url = bf.lower().replace(" ", "+")

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
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>{favicon_emoji}</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family={hf_url}:wght@400;600;700&family={bf_url}:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css">
</head>
<body>

  <!-- ═══════════ Navigation ═══════════ -->
  <nav class="nav">
    <div class="nav-inner">
      <a href="#" class="nav-logo">{favicon_emoji} {name}</a>
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

  <!-- ═══════════ Hero ═══════════ -->
  <section class="hero" id="hero">
    <div class="hero-bg">
      <img src="{t["hero_img"]}" alt="{name} — premium visual" loading="eager">
    </div>
    <div class="hero-overlay"></div>
    <div class="hero-content">
      <h1 class="fade-up">{name}</h1>
      <p class="fade-up">{subtitle}</p>
      <button class="btn btn-primary fade-up" data-scroll="features">Explore Features</button>
      <div class="hero-stats fade-up">
{stats_html}
      </div>
    </div>
  </section>

  <!-- ═══════════ About ═══════════ -->
  <section id="about">
    <div class="container">
      <h2 class="section-title fade-up">About {name}</h2>
      <p class="section-subtitle fade-up">Redefining what's possible</p>
      <div class="about-content">
{about_paragraphs}
      </div>
    </div>
  </section>

  <!-- ═══════════ Features ═══════════ -->
  <section id="features">
    <div class="container">
      <h2 class="section-title fade-up">Features &amp; Benefits</h2>
      <p class="section-subtitle fade-up">Everything you need, nothing you don't</p>
    </div>
    <div class="features-grid">
{features_html}
    </div>
  </section>

  <!-- ═══════════ Killer Feature ═══════════ -->
  <section class="killer" id="killer">
    <div class="killer-inner fade-up">
      <span class="icon">{favicon_emoji}</span>
      <h2>Why {name}?</h2>
      <p>{killer or subtitle}</p>
      <button class="btn btn-white" data-scroll="contact">Get Started Today</button>
    </div>
  </section>

  <!-- ═══════════ How It Works ═══════════ -->
  <section id="how-it-works">
    <div class="container">
      <h2 class="section-title fade-up">How It Works</h2>
      <p class="section-subtitle fade-up">Get started in just a few simple steps</p>
    </div>
    <div class="steps-container">
{steps_html}
    </div>
  </section>

  <!-- ═══════════ FAQ ═══════════ -->
  <section id="faq">
    <div class="container">
      <h2 class="section-title fade-up">Frequently Asked Questions</h2>
      <p class="section-subtitle fade-up">Got questions? We've got answers</p>
    </div>
    <div class="faq-list">
{faq_html}
    </div>
  </section>

  <!-- ═══════════ Contact ═══════════ -->
  <section id="contact">
    <div class="container">
      <h2 class="section-title fade-up">Get In Touch</h2>
      <p class="section-subtitle fade-up">We'd love to hear from you</p>
    </div>
    <div class="contact-grid">
      <form class="contact-form fade-up" id="contact-form">
        <input type="text" name="name" placeholder="Your Name" required aria-label="Your Name">
        <input type="email" name="email" placeholder="Your Email" required aria-label="Your Email">
        <textarea name="message" placeholder="Your Message" required aria-label="Your Message"></textarea>
        <button type="submit" class="btn btn-primary">Send Message</button>
      </form>
      <div class="contact-info fade-up">
        <h3>Contact Information</h3>
        <p>Have a question or want to learn more? Reach out and our team will get back to you within 24 hours.</p>
        <p>🌐 Website: <a href="{link}" style="color: {t["accent"]}; font-weight:600;">{link}</a></p>
        <p>📧 Email: hello@{link.replace("https://", "").replace("http://", "").split("/")[0] if link else "example.com"}</p>
        <div class="social-links">
          <a href="#" class="social-link" aria-label="Twitter">𝕏</a>
          <a href="#" class="social-link" aria-label="Instagram">📷</a>
          <a href="#" class="social-link" aria-label="LinkedIn">in</a>
          <a href="#" class="social-link" aria-label="Telegram">✈️</a>
        </div>
      </div>
    </div>
  </section>

  <!-- ═══════════ Footer ═══════════ -->
  <footer class="footer">
    <div class="footer-grid">
      <div class="footer-brand">
        <div class="logo">{favicon_emoji} {name}</div>
        <p>Creating exceptional experiences through innovation, quality, and attention to detail.</p>
      </div>
      <div class="footer-col">
        <h4>Quick Links</h4>
{col1_html}
      </div>
      <div class="footer-col">
        <h4>More</h4>
{col2_html}
      </div>
      <div class="footer-col">
        <h4>Connect</h4>
        <a href="#">Twitter / X</a>
        <a href="#">Instagram</a>
        <a href="#">LinkedIn</a>
        <a href="#">Telegram</a>
        <a href="{link}">Website</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; {2025} {name}. All rights reserved.</p>
      <div class="social-links">
        <a href="#" class="social-link" aria-label="Twitter" style="border-color: rgba(255,255,255,0.15); background: rgba(255,255,255,0.05); color: inherit;">𝕏</a>
        <a href="#" class="social-link" aria-label="Instagram" style="border-color: rgba(255,255,255,0.15); background: rgba(255,255,255,0.05); color: inherit;">📷</a>
        <a href="#" class="social-link" aria-label="LinkedIn" style="border-color: rgba(255,255,255,0.15); background: rgba(255,255,255,0.05); color: inherit;">in</a>
      </div>
    </div>
  </footer>

  <!-- ═══════════ Modal ═══════════ -->
  <div class="modal-overlay" id="modal-overlay">
    <div class="modal">
      <span class="icon">🚀</span>
      <h3>Coming Soon</h3>
      <p>This feature is currently in development. Stay tuned for updates!</p>
      <button class="btn btn-primary" onclick="closeModal()">Got It</button>
    </div>
  </div>

  <script src="js/script.js"></script>
</body>
</html>"""
    return html


# ──────────────────────── Main Export ────────────────────────

def generate_premium_site(
    name: str,
    description: str,
    killer_feature: str,
    analysis: dict,
    category: str,
    site_analysis: dict = None,
) -> tuple[str, str, str]:
    """Generate a premium multi-section website.

    Args:
        name: Original project name.
        description: Original project description.
        killer_feature: The standout feature of the project.
        analysis: Dict with improved_name, improved_description, killer_feature,
                  target_audience, geo_analysis, keywords, improved_link, etc.
        category: "stores", "crypto", or "companies".
        site_analysis: Optional dict from original site scraping.

    Returns:
        (html, css, js) — complete strings for index.html, css/styles.css, js/script.js
    """
    # Merge basic inputs into analysis if not already present
    if analysis is None:
        analysis = {}
    analysis.setdefault("improved_name", name)
    analysis.setdefault("improved_description", description)
    analysis.setdefault("killer_feature", killer_feature)

    cat = category if category in THEMES else "companies"
    theme = THEMES[cat]

    html = _generate_html(theme, cat, analysis, site_analysis)
    css = _generate_css(theme, cat)
    js = _generate_js(theme, cat)

    return html, css, js


# ──────────────────────── CLI Test ────────────────────────

if __name__ == "__main__":
    import json, os, zipfile, sys

    sample = {
        "improved_name": "Aurelia Atelier",
        "improved_description": "Aurelia Atelier redefines modern luxury with sustainably crafted pieces that blend Scandinavian minimalism with Mediterranean warmth. Each collection tells a story of artisanal craftsmanship, using ethically sourced materials and time-honored techniques. Our commitment to timeless design means every piece becomes a lasting part of your personal style journey.",
        "killer_feature": "Bespoke AI-powered personal styling that learns your aesthetic preferences over time",
        "improved_link": "https://aurelia-atelier.com",
        "target_audience": "Fashion-forward professionals aged 25-45 who value quality, sustainability, and unique design. Primary markets include urban centers in Europe and North America.",
        "geo_analysis": {
            "tier1": ["USA", "UK"],
            "tier2": ["France", "Germany"],
            "tier3": ["UAE"],
            "best_platforms": ["Instagram", "TikTok", "Meta Ads"],
        },
        "keywords": {
            "branded": ["Aurelia", "Aurelia Atelier"],
            "generic": ["sustainable luxury", "minimalist fashion"],
            "long_tail": ["affordable sustainable luxury clothing"],
            "competitor": ["COS", "GANNI"],
            "negative": ["fast fashion", "cheap"],
        },
    }

    for cat in ("stores", "crypto", "companies"):
        out_dir = os.path.join(os.path.dirname(__file__), "_test_output", cat)
        css_dir = os.path.join(out_dir, "css")
        js_dir = os.path.join(out_dir, "js")
        for d in (css_dir, js_dir):
            os.makedirs(d, exist_ok=True)

        html, css, js = generate_premium_site(
            name="Aurelia Atelier",
            description="Luxury fashion brand",
            killer_feature=sample["killer_feature"],
            analysis=sample,
            category=cat,
        )

        with open(os.path.join(out_dir, "index.html"), "w") as f:
            f.write(html)
        with open(os.path.join(css_dir, "styles.css"), "w") as f:
            f.write(css)
        with open(os.path.join(js_dir, "script.js"), "w") as f:
            f.write(js)

        # Also create a zip
        zip_path = os.path.join(out_dir, "..", f"site-{cat}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(os.path.join(out_dir, "index.html"), "index.html")
            zf.write(os.path.join(css_dir, "styles.css"), "css/styles.css")
            zf.write(os.path.join(js_dir, "script.js"), "js/script.js")

        print(f"✅ Generated {cat}: {out_dir}/")
        print(f"   → index.html ({len(html)} chars)")
        print(f"   → css/styles.css ({len(css)} chars)")
        print(f"   → js/script.js ({len(js)} chars)")
        print(f"   → {zip_path}")
        print()

    print("🎉 All done! Open _test_output/{category}/index.html in a browser.")
