/* eslint-env node */
const path = require('path');
const webpack = require('webpack');
const WebpackManifestPlugin = require('webpack-yam-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const assetRootPath = path.resolve(__dirname, 'app', 'static');

const config = (env, argv) => {
    const isDev = argv.mode === 'development';
    return {
        devtool: isDev ? 'eval-source-map' : 'source-map',
        entry: path.resolve(assetRootPath, 'natlas.js'),
        watchOptions: {
            // Ignore node_modules and output folder
            ignored: /node_modules|static\/dist/,
        },
        module: {
            rules: [
                {
                    parser: {
                        amd: false
                    }
                },
                {
                    exclude: /node_modules/,
                    test: /\.ts$/,
                    use: 'ts-loader'
                },
                {
                    test: /\.(sass|scss|css)$/,
                    use: [
                        MiniCssExtractPlugin.loader,
                        'css-loader',
                        {
                            loader: 'postcss-loader',
                            options: {
                                postcssOptions: {
                                    plugins: [
                                        'tailwindcss',
                                        'autoprefixer'
                                    ]
                                }
                            }
                        },
                        'sass-loader'
                    ]
                },
                {
                    test: /\.(svg|eot|woff|woff2|ttf)(\?v=\d+\.\d+\.\d+)?$/,
                    use: 'file-loader?publicPath=/static/dist'
                }
            ]
        },
        output: {
            filename: '[name].js',
            path: path.resolve(assetRootPath, 'dist')
        },
        plugins: [
            new MiniCssExtractPlugin(),
            new WebpackManifestPlugin({
                manifestPath: path.resolve(assetRootPath, 'dist', 'webpack_manifest.json'),
                outputRoot: assetRootPath
            }),
            new webpack.EnvironmentPlugin({
                NATLAS_VERSION: "dev"
            })
        ],
        resolve: {
            extensions: ['.ts', '.js'],
            modules: [
                'static',
                'node_modules'
            ]
        }
    };
};

module.exports = config;
