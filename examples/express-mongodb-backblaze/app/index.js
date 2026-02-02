const express = require('express');
const { MongoClient, ObjectId } = require('mongodb');

const MONGO_URI = process.env.MONGO_URI;
const MONGO_DATABASE = process.env.MONGO_DATABASE;

if (!MONGO_URI || !MONGO_DATABASE) {
  console.error('MONGO_URI and MONGO_DATABASE environment variables are required');
  process.exit(1);
}

const app = express();
app.use(express.json());

let db;
let todosCollection;

async function connectToDatabase() {
  const client = new MongoClient(MONGO_URI);
  await client.connect();
  db = client.db(MONGO_DATABASE);
  todosCollection = db.collection('todos');
  console.log(`Connected to MongoDB database: ${MONGO_DATABASE}`);
}

// Health check
app.get('/', (req, res) => {
  res.json({ message: 'Todo API - MongoDB backed up by NestVault' });
});

// List all todos
app.get('/todos', async (req, res) => {
  try {
    const todos = await todosCollection.find({}).toArray();
    res.json(todos);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create a todo
app.post('/todos', async (req, res) => {
  try {
    const { title, completed = false } = req.body;
    if (!title) {
      return res.status(400).json({ error: 'Title is required' });
    }
    const result = await todosCollection.insertOne({ title, completed });
    const todo = await todosCollection.findOne({ _id: result.insertedId });
    res.status(201).json(todo);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get a todo by ID
app.get('/todos/:id', async (req, res) => {
  try {
    const todo = await todosCollection.findOne({ _id: new ObjectId(req.params.id) });
    if (!todo) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json(todo);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update a todo
app.put('/todos/:id', async (req, res) => {
  try {
    const { title, completed } = req.body;
    const update = {};
    if (title !== undefined) update.title = title;
    if (completed !== undefined) update.completed = completed;

    const result = await todosCollection.findOneAndUpdate(
      { _id: new ObjectId(req.params.id) },
      { $set: update },
      { returnDocument: 'after' }
    );
    if (!result) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete a todo
app.delete('/todos/:id', async (req, res) => {
  try {
    const result = await todosCollection.deleteOne({ _id: new ObjectId(req.params.id) });
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json({ message: 'Todo deleted' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Health endpoint
app.get('/health', async (req, res) => {
  try {
    await db.admin().ping();
    res.json({ status: 'healthy', database: 'connected' });
  } catch (error) {
    res.json({ status: 'unhealthy', database: error.message });
  }
});

const PORT = process.env.PORT || 3000;

connectToDatabase()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  })
  .catch((error) => {
    console.error('Failed to connect to database:', error);
    process.exit(1);
  });
