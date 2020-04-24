/* eslint-env node */
const path = require('path');
const WebpackManifestPlugin = require('webpack-yam-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const assetRootPath = path.resolve(__dirname, 'app', 'static');

const config = {
	entry: path.resolve(assetRootPath, 'natlas.js'),
	module: {
		rules: [
			{
				parser: {
					amd: false
				}
			},
			{
				test: /\.ts$/,
				use: 'ts-loader',
				exclude: /node_modules/
			},
			{
				test: /\.(sass|scss|css)$/,
				use: [
					MiniCssExtractPlugin.loader,
					'css-loader',
					'sass-loader'
				]
			},
			{
				test: /\.(svg|eot|woff|woff2|ttf)(\?v=\d+\.\d+\.\d+)?$/,
				use: [
					'file-loader?publicPath=/static/dist'
				]
			}
		]
	},
	resolve: {
		extensions: ['.ts', '.js'],
		modules: [
			'static',
			'node_modules'
		]
	},
	output: {
		path: path.resolve(assetRootPath, 'dist'),
		filename: '[name].js'
	},
	plugins: [
		new MiniCssExtractPlugin(),
		new WebpackManifestPlugin({
			manifestPath: path.resolve(assetRootPath, 'dist', 'webpack_manifest.json'),
			outputRoot: assetRootPath
		})
	]
};

module.exports = config;
