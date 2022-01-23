export default {
    version: 'v1',
    root: 'https://us-central1-intime-frontend.cloudfunctions.net/api',
    get news() {
        return `${this.root}/${this.version}/news`;
    }
}