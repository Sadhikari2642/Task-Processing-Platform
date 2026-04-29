const User = require('../models/User');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const config = require('../config');

exports.register = async (req, res) => {
  const { email, password } = req.body;
  const existing = await User.findOne({ email });
  if (existing) return res.status(400).json({ error: 'Exists' });
  const hash = await bcrypt.hash(password, 10);
  const u = await User.create({ email, passwordHash: hash });
  const token = jwt.sign({ id: u._id, email: u.email }, config.jwtSecret, { expiresIn: '7d' });
  res.json({ token });
};

exports.login = async (req, res) => {
  const { email, password } = req.body;
  const u = await User.findOne({ email });
  if (!u) return res.status(400).json({ error: 'Invalid' });
  const ok = await u.verify(password);
  if (!ok) return res.status(400).json({ error: 'Invalid' });
  const token = jwt.sign({ id: u._id, email: u.email }, config.jwtSecret, { expiresIn: '7d' });
  res.json({ token });
};
