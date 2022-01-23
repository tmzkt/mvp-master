const path = require('path');
const VueLoaderPlugin = require('vue-loader/lib/plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const isDevMode = process.env.NODE_ENV !== 'production';
const rootDir = './mvp_project';

module.exports = {
    mode: isDevMode ? 'development' : 'production',
    entry: {
        ticker: `${rootDir}/src/components/ticker`,
        reviews: `${rootDir}/src/components/reviews`,
        stats: `${rootDir}/src/modules/antivirus/stats.js`,
    },
    output: {
        filename: '[name]/js/app.js',
        path: path.resolve(__dirname, '../static/components'),
    },
    plugins: [
        new VueLoaderPlugin(),
        /* new MiniCssExtractPlugin({
            filename: '../../css/[name].css'
        }), */
    ],
    module: {
        rules: [
            {
                test: /\.js$/,
                use: 'babel-loader',
            },
            {
                test: /\.vue$/,
                use: 'vue-loader',
            },
            {
                resourceQuery: /blockType=i18n/,
                type: 'javascript/auto',
                loader: '@kazupon/vue-i18n-loader'
            },
            {
                test: /\.scss$/,
                use: [
                    /* MiniCssExtractPlugin.loader, */
                    'vue-style-loader',
                    'css-loader',
                    {
                        loader: 'postcss-loader',
                        options: { sourceMap: isDevMode }
                    },
                    {
                        loader: 'sass-loader',
                        options: {
                            sourceMap: isDevMode,
                            implementation: require('sass'),
                        },
                    }

                ],
            },
        ]
    },
    watch: isDevMode,
    watchOptions: {
        ignored: /node_modules/
    },
    devtool: isDevMode && 'inline-source-map',
};