import { MongoClient } from 'mongodb';
import fs from 'fs';
import dotenv from 'dotenv';
dotenv.config();

const client = new MongoClient(process.env.MONGODB_URI);

const db = client.db('edithunt');
const collection = db.collection('leads');

const leads = await collection.find({}).toArray();

//save json
fs.writeFileSync('leads.json', JSON.stringify(leads, null, 2));

client.close();