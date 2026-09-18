const products = require('../../data/products.json');

module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=300');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

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
