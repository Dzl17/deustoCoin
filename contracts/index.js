const Web3 = require('web3');
const web3 = new Web3('http://localhost:9545');

const conract = new web3.eth.Contract(
    abi,
    address
);