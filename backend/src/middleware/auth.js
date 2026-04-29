const jwt = require('jsonwebtoken');
const config = require('../config');

module.exports = function(req, res, next){
  const h = req.headers.authorization;
  if(!h) return res.status(401).json({ error: 'Missing token' });
  const token = h.replace('Bearer ', '');
  try{
    const payload = jwt.verify(token, config.jwtSecret);
    req.user = payload;
    next();
  }catch(e){
    return res.status(401).json({ error: 'Invalid token' });
  }
};
