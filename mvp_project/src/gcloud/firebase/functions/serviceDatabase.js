const _ = require('lodash');

const getSnapshot = snapshot => key => snapshot.child(key).val();

exports.getSnapshot = getSnapshot;

exports.calcTopSlugs = snapshot => {
    const snapshotByKey = getSnapshot(snapshot);
    const countires = snapshotByKey('summary').Countries;
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
