const { google } = require('googleapis');

const sheet = google.sheets({
    version: 'v4',
    auth: 'AIzaSyBGV6Ox8ircJ5pN6LsW4LEF9Bc7Ztq2xfs',
});
const request = sheet.spreadsheets.values.get({
    spreadsheetId: '1pCszLxV9IjhdhG0AqTS69YuctLYx3PM0hEbBbjjw_d8',
    range: 'news',
});

exports.getNews = () => (
    request.then(
        response => {
            const { values } = response.data;

            return values.map(value => ({ title: value[0], url: value[1] }));
        },
        reason => console.error('error: ' + reason.result.error.message)).catch(err => console.error(err)
        )
);
