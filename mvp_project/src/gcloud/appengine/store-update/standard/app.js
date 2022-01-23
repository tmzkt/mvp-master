// Copyright 2017 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

'use strict';

const express = require('express');
const app = express();
app.enable('trust proxy');

const { Datastore } = require('@google-cloud/datastore');
const Firestore = require('@google-cloud/firestore');

// Instantiate a datastore client
const datastore = new Datastore();
const firestore = new Firestore();

app.get('/', async (req, res) => {
  await updateData(new Date());
  res.status(200).send('Data update!').end();
});

async function updateData(dataDate) {
  async function setLastModified() {
    const transaction = datastore.transaction();
    const key = datastore.key(['antivirus', 'stats']);
    console.log(key);
    console.log(key.path);
    try {
      await transaction.run();
      const [task] = await transaction.get(key);
      task.done = true;
      task.date = dataDate;
      transaction.save({
        key: key,
        data: task,
      });
      await transaction.commit();
      console.log(`Task ${dataDate} updated successfully.`);
    } catch (err) {
      transaction.rollback();
      throw err;
    }
  }
  setLastModified();
}

// Start the server
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`App listening on port ${PORT}`);
  console.log('Press Ctrl+C to quit.');
});

module.exports = app;
