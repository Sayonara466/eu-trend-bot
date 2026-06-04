// Vercel Serverless - запускается каждый раз при запросе
// Но для Telegram polling это не подходит - нужен webhook

export default async function handler(req, res) {
  if (req.method === 'POST') {
    // Telegram webhook handler
    const update = req.body;
    console.log('Webhook update:', JSON.stringify(update).substring(0, 200));
    res.status(200).json({ ok: true });
  } else {
    res.status(200).send('EU Trend Bot webhook');
  }
}
