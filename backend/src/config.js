const dotenv = require('dotenv');
dotenv.config();

module.exports = {
  port: process.env.PORT || 4000,
  jwtSecret: process.env.JWT_SECRET || 'changeme',
  mongoUri: process.env.MONGO_URI || 'mongodb://mongo:27017/tasks',
  redisUrl: process.env.REDIS_URL || 'redis://redis:6379',
  redisQueue: process.env.REDIS_QUEUE || 'tasks:queue'
};
