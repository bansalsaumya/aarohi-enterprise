const products = require('../data/products.json');

module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=300');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Check if this is a single product request (e.g. via ?slug=... or url path)
  const urlParts = req.url.split('?')[0].split('/').filter(Boolean);
  let slug = req.query.slug;
  if (!slug && urlParts.length > 2 && urlParts[1] === 'products') {
    slug = urlParts.slice(2).join('/');
  }

  if (slug) {
    const rawSlug = decodeURIComponent(String(slug)).trim();
    const normalizedSlug = rawSlug.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

    const product = products.find(p => {
      if (p.slug === rawSlug || p.slug === normalizedSlug) return true;
      if (String(p.id) === rawSlug) return true;
      if (p.name && p.name.toLowerCase() === rawSlug.toLowerCase()) return true;
      if (p.name && p.name.toLowerCase().replace(/[^a-z0-9]+/g, '-') === normalizedSlug) return true;
      return false;
    });

    if (product) {
      return res.status(200).json(product);
    }

    const partialMatch = products.find(p => 
      p.slug.includes(normalizedSlug) || (p.name && p.name.toLowerCase().includes(rawSlug.toLowerCase()))
    );
    if (partialMatch) {
      return res.status(200).json(partialMatch);
    }
    return res.status(404).json({ error: 'Product not found' });
  }

  // Otherwise return products list
  const { category, featured, search, q } = req.query || {};
  let filtered = [...products];

  if (category) {
    filtered = filtered.filter(p => p.category_slug === category || String(p.category_id) === String(category));
  }

  if (featured === 'true' || featured === '1') {
    filtered = filtered.filter(p => p.is_featured === 1);
  }

  const searchTerm = search || q;
  if (searchTerm) {
    const s = searchTerm.toLowerCase();
    filtered = filtered.filter(p => 
      (p.name && p.name.toLowerCase().includes(s)) || 
      (p.description && p.description.toLowerCase().includes(s)) ||
      (p.category_name && p.category_name.toLowerCase().includes(s))
    );
  }

  res.status(200).json(filtered);
};
