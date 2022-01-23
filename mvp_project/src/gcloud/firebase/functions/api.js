exports.serviceApi = {
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
