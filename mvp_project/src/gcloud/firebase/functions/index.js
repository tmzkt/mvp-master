const functions = require('firebase-functions');
const admin = require("firebase-admin");
const express = require('express');
const fetch = require('node-fetch');
const bodyParser = require('body-parser');
const cors = require('cors');

const sheets = require('./sheets');
const serviceApi = require('./api').serviceApi;
const getSnapshot = require('./serviceDatabase').getSnapshot;
const calcTopSlugs = require('./serviceDatabase').calcTopSlugs;

admin.initializeApp();

const app = express();
const main = express();

const rootKey = 'antivirus';
const database = admin.database();
const antivirusRef = database.ref(rootKey);
const intimeRef = database.ref('intime');
const writeToDatabase = keyDatabase => res => {
    return database.ref(`${rootKey}/${keyDatabase}`).set(res);
};

const VER_API = 'v1';
const SLUGS = {
    SYMPTOMS: 'symptoms',
    ADVICES: 'advices',
    LATEST: 'latest',
    NEWS: 'news',
};

const getLatestData = () => {
    const loadDataCountry = topSlugs => {
        topSlugs.forEach(async (el, i) => {
            const resFetch = await fetch(serviceApi.confirmed(el.slug));
            const json = await resFetch.json();
            writeToDatabase(serviceApi.confirmed(el.slug, true))(json);
        });
    };

    return fetch(serviceApi.summary())
        .then(res => res.json())
        .then(json => {
            writeToDatabase(serviceApi.summary(true))(json);
            return null;
        })
        .catch(err => console.error(err))
        .then(() => {
            return antivirusRef.once('value').then(snapshot => {
                const topSlugs = calcTopSlugs(snapshot);
                writeToDatabase('topSlugs')(topSlugs);
                writeToDatabase('lastModified')(new Date().toUTCString());
                loadDataCountry(topSlugs);

                return null;
            }).catch(err => console.error(err))
        });
};

exports.schedule = functions.pubsub.schedule('every 24 hours').onRun((context) => {
    getLatestData();
    return null;
});

exports.forceUpdate = functions.https.onRequest((request, response) => {
    getLatestData();
    response.send('Force update');
});

exports.writeData = functions.https.onRequest(async (request, response) => {
    const symptoms = {
        ru: {
            title: 'Общие симптомы включают в себя',
            list: [
                'высокая температура',
                'усталость',
                'сухой кашель',
                'одышка',
                'ломота и боль',
                'больное горло',
                'очень немногие сообщают о диарее, тошноте или насморке',
            ]
        },
        en: {
            title: 'WHO COVID-19 symptoms include',
            list: [
                'fever',
                'tiredness',
                'dry cough',
                'shortness of breath',
                'aches and pains',
                'sore throat',
                'very few people will report diarrhoea, nausea or a runny nose',
            ]
        }
    };
    const advices = {
        ru: {
            title: 'Советы ВОЗ по COVID-19',
            list: [
                'Мойте руки как можно чаще при помощи мыла и воды (продолжительность &gt; 40 сек) или спиртосодержащих средств (содержание спирта & gt; 60%)',
                'Соблюдайте социальную дистанцию 1,5 метра и больше',
                'Избегайте прикасаться к глазам, носу и рту',
                'Если у Вас повышенная температура, кашель и признаки затрудненного дыхания, обращайтесь за медицинской помощью как можно скорее',
                'Следуйте правилам респираторной гигиены (закрывайте рот и нос во время чихания или кашля салфетками или тканью, после чего сразу избавляйтесь от них)',
                'Продолжайте получать информацию и следовать указаниям медицинских служб.',
            ]
        },
        en: {
            title: 'WHO COVID-19 advices',
            list: [
                'Wash your hands frequently',
                'Maintain social distancing',
                'Avoid touching eyes, nose and mouth',
                'Practice respiratory hygiene',
                'If you have fever, cough and difficulty breathing, seek medical care early',
                'Stay informed and follow advice given by your healthcare provider',
            ]
        }
    };
    await database.ref(`${rootKey}/symptoms`).set(symptoms);
    await database.ref(`${rootKey}/advices`).set(advices);

    response.send('Data update');
});

app.use(cors({ origin: true }));
main.use(`/${VER_API}`, app);
main.use(bodyParser.json());
main.use(bodyParser.urlencoded({ extended: false }));

exports.api = functions.https.onRequest(main);

main.get('/', (request, response) => {
    let list = '';
    for (const key in SLUGS) {
        if (SLUGS.hasOwnProperty(key)) {
            list +=
                `
                    <li style="margin-bottom: 10px;">
                        <a href="api/${VER_API}/${SLUGS[key]}">${SLUGS[key]}</a>
                    </li>
                `;
        }
    }
    const html = `<ul style="padding: 20px 42px;">${list}</ul>`;

    response.send(html);
});

app.get('/symptoms', (request, response) => {
    antivirusRef.once('value').then((snapshot) => {
        const symptoms = getSnapshot(snapshot)(`symptoms`);

        return response.status(200).json(symptoms);
    }).catch(err => console.error(err));
});

app.get('/advices', (request, response) => {
    antivirusRef.once('value').then((snapshot) => {
        const advices = getSnapshot(snapshot)(`advices`);

        return response.status(200).json(advices);
    }).catch(err => console.error(err));
});

app.get('/latest', (request, response) => {
    antivirusRef.once('value').then((snapshot) => {
        const topSlugs = getSnapshot(snapshot)(`topSlugs`);

        return response.send(topSlugs);
    }).catch(err => console.error(err));
});

app.get('/news', async (request, response) => {
    const isOverwrited = request.query.overwrite === '1';

    if (isOverwrited) {
        const dataSheets = await sheets.getNews();
        const renderResponseFromSnapshot = snapshot => {
            const news = getSnapshot(snapshot)('news');
            const renderNews = news => `<a target='_blank;' href='${news.url}'>${news.title}</a>`;
            const preparedNews = `<div style='padding: 30px; display: flex; flex-direction: column;'>${news.map(renderNews)}</div>`;
            const content = isOverwrited ? preparedNews : news;

            return response.status(200).send(content);
        }

        database
            .ref('intime/news')
            .set(dataSheets)
            .then(() => intimeRef.once('value').then(renderResponseFromSnapshot).catch(err => console.error(err))
            ).catch(err => console.error(err))
    } else {
        intimeRef.once('value').then((snapshot) => {
            const news = getSnapshot(snapshot)('news');

            return response.status(200).send(news);
        }).catch(err => console.error(err));
    }
});
