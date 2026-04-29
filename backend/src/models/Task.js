const mongoose = require('mongoose');

const TaskSchema = new mongoose.Schema({
  userId: { type: mongoose.Types.ObjectId, required: true, index: true },
  title: String,
  inputText: String,
  operation: { type: String, enum: ['uppercase','lowercase','reverse','wordcount'] },
  status: { type: String, enum: ['pending','running','success','failed'], default: 'pending', index: true },
  result: mongoose.Schema.Types.Mixed,
  logs: [String],
  retries: { type: Number, default: 0 },
  createdAt: { type: Date, default: Date.now, index: true },
  updatedAt: { type: Date, default: Date.now }
});

TaskSchema.pre('save', function(next){ this.updatedAt = Date.now(); next(); });

module.exports = mongoose.model('Task', TaskSchema);
