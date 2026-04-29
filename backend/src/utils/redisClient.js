const Redis = require('ioredis');
const config = require('../config');

const redis = new Redis(config.redisUrl);
module.exports = redis;
