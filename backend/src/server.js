const mongoose = require('mongoose');
const config = require('./config');
const app = require('./app');

mongoose.connect(config.mongoUri, { autoIndex: true })
  .then(() => {
    app.listen(config.port, () => console.log('API listening on', config.port));
  })
  .catch(err => {
    console.error('Mongo connect error', err);
    process.exit(1);
  });
