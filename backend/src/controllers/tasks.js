const Task = require('../models/Task');
const redis = require('../utils/redisClient');
const config = require('../config');

exports.create = async (req, res) => {
  const { title, inputText, operation } = req.body;
  const task = await Task.create({ userId: req.user.id, title, inputText, operation });
  // push string task id + timestamp to redis list for recovery logic
  await redis.lpush(config.redisQueue, JSON.stringify({ taskId: task._id.toString(), ts: new Date().toISOString() }));
  res.json({ id: task._id });
};

exports.list = async (req, res) => {
  const tasks = await Task.find({ userId: req.user.id }).sort({ createdAt: -1 }).limit(100);
  res.json(tasks);
};

exports.get = async (req, res) => {
  const task = await Task.findOne({ _id: req.params.id, userId: req.user.id });
  if (!task) return res.status(404).end();
  res.json(task);
};
