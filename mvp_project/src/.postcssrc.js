module.exports = {
    plugins: {
        'postcss-preset-env': { stage: 2, features: { 'custom-media-queries': true } },
        'cssnano': { preset: ['default', { normalizePositions: false }] }
    }
}