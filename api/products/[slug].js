const products = require('../../data/products.json');

module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=300');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { slug } = req.query || {};
  if (!slug) {
    return res.status(400).json({ error: 'Product slug is required' });
  }

  const rawSlug = decodeURIComponent(String(slug)).trim();
  const normalizedSlug = rawSlug.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

  const product = products.find(p => {
    if (p.slug === rawSlug || p.slug === normalizedSlug) return true;
    if (String(p.id) === rawSlug) return true;
    if (p.name && p.name.toLowerCase() === rawSlug.toLowerCase()) return true;
    if (p.name && p.name.toLowerCase().replace(/[^a-z0-9]+/g, '-') === normalizedSlug) return true;
    return false;
  });

  if (!product) {
    // Fallback search
    const partialMatch = products.find(p => 
      p.slug.includes(normalizedSlug) || (p.name && p.name.toLowerCase().includes(rawSlug.toLowerCase()))
    );
    if (partialMatch) {
      return res.status(200).json(partialMatch);
    }
    return res.status(404).json({ error: 'Product not found' });
  }

  res.status(200).json(product);
};
