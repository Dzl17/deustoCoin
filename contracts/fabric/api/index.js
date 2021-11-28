'use strict';

require('dotenv').config();
const express = require('express');

const { Gateway, Wallets } = require('fabric-network');
const FabricCAServices = require('fabric-ca-client');
const path = require('path');
const { buildCAClient, registerAndEnrollUser, enrollAdmin } = require('./utils/CAUtil');
const {buildCCPOrg1, buildWallet } = require('./utils/AppUtil');

const channelName = 'mychannel';
const chaincodeName = 'basic';
const mspOrg1 = 'Org1MSP';
const walletPath = path.join(__dirname, 'wallet');
const org1UserId = 'appUser';

const prettifyJSON = inputString => {
	return JSON.stringify(JSON.parse(inputString), null, 4);
}


const app = express();

const requestLogger = (request, response, next) => {
    console.log(`${request.method} - ${request.path}, data: ${request.body}`);
    next();
}

const unknownEndpoint = (request, response) => {
    response.status(404).send({ error: 'unknown endpoint' });
}


app.use(express.json());
app.use(requestLogger);

app.get('/', async (request, response) => {
    response.json(
        {
            "get_requests": {
                "token_name": "/api/name",
                "token_symbol": "/api/symbol",
                "token_decimals": "/api/decimals",
                "balance_of": "/api/balance/<address>"
            },
            "post_requests": {
                "transfer": "/api/transfer",
                "mint": "/api/mint",
                "burn": "/api/burn",
                "process_action": "/api/process-action"
            }
        }
    );
});

app.get('/api/name', async (request, response) => {

});

app.get('/api/symbol', async (request, response) => {

});

app.get('/api/decimals', async (request, response) => {

});

app.get('/api/balance/:address', async (request, response) => {

});

app.post('/api/transfer', async (request, response) => {

});

app.post('/api/mint', async (request, response) => {

});

app.post('/api/burn', async (request, response) => {

});

app.post('/api/process-action', async (request, response) => {

});


app.use(unknownEndpoint);

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Direct URL: http://localhost:${PORT}`);
});