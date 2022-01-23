const express = require('express');
const fetch = require('node-fetch');
const cron = require('node-cron');
const firebase = require('firebase');
const _ = require('lodash');
require('firebase/database');
const config = require('./firebaseConfig.js');

const app = express();
const port = 3000;

firebase.initializeApp(config);

const rootKey = 'antivirus';
const database = firebase.database();
const antivirusRef = database.ref(rootKey);
const getSnapshotChild = snapshot => key => snapshot.child(key).val();
const writeToDatabase = keyDatabase => res => {
    return database.ref(`${rootKey}/${keyDatabase}`).set(res);
};
const api = {
    root: 'https://api.covid19api.com',
    summary(isKey = false) {
        const key = 'summary';
        return isKey ? key : `${this.root}/${key}`;
    },
    confirmed(geo, isKey = false) {
        const key = `total/country/${geo}/status/confirmed`;
        return isKey ? key : `${this.root}/${key}`;
    },
};

const calcTopSlugs = snapshot => {
    const snapshotByKey = getSnapshotChild(snapshot);
    const countires = snapshotByKey(`summary`).Countries;
    const sorteringByTotal = _.orderBy(
        countires,
        ['TotalConfirmed'],
        ['desc']
    );
    const topSlugs = sorteringByTotal
        .splice(0, 21)
        .map(item => ({ slug: item.Slug, name: item.Country, total: item.TotalConfirmed }));

    return topSlugs;
};

const getLatestData = () => {
    const loadDataCountry = topSlugs => {
        topSlugs.forEach(async (el, i) => {
            const resFetch = await fetch(api.confirmed(el.slug));
            const json = await resFetch.json();
            writeToDatabase(api.confirmed(el.slug, true))(json);
        });
    };

    return fetch(api.summary())
        .then(res => res.json())
        .then(json => {
            writeToDatabase(api.summary(true))(json);
        }).finally(() => {
            antivirusRef.once('value').then(snapshot => {
                const topSlugs = calcTopSlugs(snapshot);
                writeToDatabase('topSlugs')(topSlugs);
                writeToDatabase('lastModified')(new Date().toUTCString());
                loadDataCountry(topSlugs);
            })
        });
}

cron.schedule('*/2 * * * *', getLatestData);

app.get('/top-slugs', (request, response) => {
    antivirusRef.once('value').then(snapshot => {
        response.send(calcTopSlugs(snapshot));
    })
});

app.get('/latest', (request, response) => {
    getLatestData();
});

app.listen(port, () => console.log(`Start parser.js ${port}`));