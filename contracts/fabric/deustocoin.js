'use strict';

const { Contract } = require('fabric-contract-api');

// Define objectType names for prefix
const balancePrefix = 'balance';

// Define key names for options
const nameKey = 'Deustocoin';
const symbolKey = 'UDC';
const decimalsKey = '2';
const totalSupplyKey = 'totalSupply';

// Define other constants
const adminMSP = 'udMSP';

class DeustocoinContract extends Contract {

    /**
     * Return the name of the token.
     *
     * @param {Context} ctx the transaction context
     * @returns {String} Returns the name of the token
    */
    async tokenName(ctx) {
        const nameBytes = await ctx.stub.getState(nameKey);
        return nameBytes.toString();
    }

    /**
     * Return the symbol of the token.
     *
     * @param {Context} ctx the transaction context
     * @returns {String} Returns the symbol of the token
    */
    async symbol(ctx) {
        const symbolBytes = await ctx.stub.getState(symbolKey);
        return symbolBytes.toString();
    }

    /**
     * Return the number of decimals the token uses.
     *
     * @param {Context} ctx the transaction context
     * @returns {Number} Returns the number of decimals
    */
    async decimals(ctx) {
        const decimalsBytes = await ctx.stub.getState(decimalsKey);
        return parseInt(decimalsBytes.toString());
    }

    /**
     * Return the total token supply.
     *
     * @param {Context} ctx the transaction context
     * @returns {Number} Returns the total token supply
    */
    async totalSupply(ctx) {
        const totalSupplyBytes = await ctx.stub.getState(totalSupplyKey);
        return parseInt(totalSupplyBytes.toString());
    }

    /**
     * BalanceOf returns the balance of the given account.
     *
     * @param {Context} ctx the transaction context
     * @param {String} owner The owner from which the balance will be retrieved
     * @returns {Number} Returns the account balance
     */
    async balanceOf(ctx, owner) {
        const balanceKey = ctx.stub.createCompositeKey(balancePrefix, [owner]);

        const balanceBytes = await ctx.stub.getState(balanceKey);
        if (!balanceBytes || balanceBytes.length === 0) {
            throw new Error(`the account ${owner} does not exist`);
        }
        const balance = parseInt(balanceBytes.toString());

        return balance;
    }

    /**
     *  Transfer transfers tokens from client account to recipient account.
     *  recipient account must be a valid clientID as returned by the ClientAccountID() function.
     *
     * @param {Context} ctx the transaction context
     * @param {String} to The recipient
     * @param {Integer} value The amount of token to be transferred
     * @returns {Boolean} Return whether the transfer was successful or not
     */
    async transfer(ctx, to, value) {
        const from = ctx.clientIdentity.getID();

        const transferResp = await this._transfer(ctx, from, to, value);
        if (!transferResp) {
            throw new Error('Failed to transfer');
        }

        // Emit the Transfer event
        const transferEvent = { from, to, value: parseInt(value) };
        ctx.stub.setEvent('Transfer', Buffer.from(JSON.stringify(transferEvent)));

        return true;
    }

    /**
     *  Internal helper function to carry out transactions
     * 
     * @param {Context} ctx the transaction context
     * @param {String} from the sender
     * @param {String} to the recipient
     * @param {Integer} value the amount of token to be transferred
     * @returns {Boolean} Return wheter the transfer was succesful or not
     */
    async _transfer(ctx, from, to, value) {
        if (from === to) {
            throw new Error('cannot transfer to and from same client account');
        }

        const valueInt = parseInt(value);
        if (valueInt < 0) {
            throw new Error('transfer amount cannot be negative');
        }

        // Retrieve sender balance
        const fromBalanceKey = ctx.stub.createCompositeKey(balancePrefix, [from]);
        const fromCurrentBalanceBytes = await ctx.stub.getState(fromBalanceKey);

        if (!fromCurrentBalanceBytes || fromCurrentBalanceBytes.length === 0) {
            throw new Error(`client account ${from} has no balance`);
        }

        const fromCurrentBalance = parseInt(fromCurrentBalanceBytes.toString());

        // Check if sender has enough funds
        if (fromCurrentBalance < valueInt) {
            throw new Error(`client account ${from} has insufficient funds.`);
        }

        // Retrieve recepient balance
        const toBalanceKey = ctx.stub.createCompositeKey(balancePrefix, [to]);
        const toCurrentBalanceBytes = await ctx.stub.getState(toBalanceKey);

        let toCurrentBalance;
        // Create recepient balance if it doesn't exist yet
        if (!toCurrentBalanceBytes || toCurrentBalanceBytes.length === 0) {
            toCurrentBalance = 0;
        } else {
            toCurrentBalance = parseInt(toCurrentBalanceBytes.toString());
        }

        // Update the balances
        const fromUpdatedBalance = fromCurrentBalance - valueInt;
        const toUpdatedBalance = toCurrentBalance + valueInt;

        await ctx.stub.putState(fromBalanceKey, Buffer.from(fromUpdatedBalance.toString()));
        await ctx.stub.putState(toBalanceKey, Buffer.from(toUpdatedBalance.toString()));

        console.log(`client ${from} balance updated from ${fromCurrentBalance} to ${fromUpdatedBalance}`);
        console.log(`recipient ${to} balance updated from ${toCurrentBalance} to ${toUpdatedBalance}`);

        return true;
    }

    /**
     * Set optional infomation for a token.
     *
     * @param {Context} ctx the transaction context
     * @param {String} name The name of the token
     * @param {String} symbol The symbol of the token
     * @param {String} decimals The decimals of the token
     * @param {String} totalSupply The totalSupply of the token
     */
    async SetOption(ctx, name, symbol, decimals) {
        await ctx.stub.putState(nameKey, Buffer.from(name));
        await ctx.stub.putState(symbolKey, Buffer.from(symbol));
        await ctx.stub.putState(decimalsKey, Buffer.from(decimals));

        console.log(`name: ${name}, symbol: ${symbol}, decimals: ${decimals}`);
        return true;
    }

    /**
     * Mint creates new tokens and adds them to minter's account balance
     *
     * @param {Context} ctx the transaction context
     * @param {Integer} amount amount of tokens to be minted
     * @returns {Object} The balance
     */
    async mint(ctx, amount) {

        // Check minter authorization - this sample assumes 'ud' is the central banker with privilege to mint new tokens
        const clientMSPID = ctx.clientIdentity.getMSPID();
        if (clientMSPID !== adminMSP) {
            throw new Error('client is not authorized to mint new tokens');
        }

        // Get ID of submitting client identity
        const minter = ctx.clientIdentity.getID();

        const amountInt = parseInt(amount);
        if (amountInt <= 0) {
            throw new Error('mint amount must be a positive integer');
        }

        const balanceKey = ctx.stub.createCompositeKey(balancePrefix, [minter]);

        const currentBalanceBytes = await ctx.stub.getState(balanceKey);
        // If minter current balance doesn't yet exist, we'll create it with a current balance of 0
        let currentBalance;
        if (!currentBalanceBytes || currentBalanceBytes.length === 0) {
            currentBalance = 0;
        } else {
            currentBalance = parseInt(currentBalanceBytes.toString());
        }
        const updatedBalance = currentBalance + amountInt;

        await ctx.stub.putState(balanceKey, Buffer.from(updatedBalance.toString()));

        // Increase totalSupply
        const totalSupplyBytes = await ctx.stub.getState(totalSupplyKey);
        let totalSupply;
        if (!totalSupplyBytes || totalSupplyBytes.length === 0) {
            console.log('Initialize the tokenSupply');
            totalSupply = 0;
        } else {
            totalSupply = parseInt(totalSupplyBytes.toString());
        }
        totalSupply = totalSupply + amountInt;
        await ctx.stub.putState(totalSupplyKey, Buffer.from(totalSupply.toString()));

        // Emit the Transfer event
        const transferEvent = { from: '0x0', to: minter, value: amountInt };
        ctx.stub.setEvent('Transfer', Buffer.from(JSON.stringify(transferEvent)));

        console.log(`minter account ${minter} balance updated from ${currentBalance} to ${updatedBalance}`);
        return true;
    }

    /**
     * Burn redeem tokens from minter's account balance
     *
     * @param {Context} ctx the transaction context
     * @param {Integer} amount amount of tokens to be burned
     * @returns {Object} The balance
     */
    async Burn(ctx, amount) {
        // Check minter authorization - this sample assumes 'ud'' is the central banker with privilege to burn tokens
        const clientMSPID = ctx.clientIdentity.getMSPID();
        if (clientMSPID !== adminMSP) {
            throw new Error('client is not authorized to mint new tokens');
        }

        const minter = ctx.clientIdentity.getID();

        const amountInt = parseInt(amount);

        const balanceKey = ctx.stub.createCompositeKey(balancePrefix, [minter]);

        const currentBalanceBytes = await ctx.stub.getState(balanceKey);
        if (!currentBalanceBytes || currentBalanceBytes.length === 0) {
            throw new Error('The balance does not exist');
        }
        const currentBalance = parseInt(currentBalanceBytes.toString());
        const updatedBalance = currentBalance - amountInt;

        await ctx.stub.putState(balanceKey, Buffer.from(updatedBalance.toString()));

        // Decrease totalSupply
        const totalSupplyBytes = await ctx.stub.getState(totalSupplyKey);
        if (!totalSupplyBytes || totalSupplyBytes.length === 0) {
            throw new Error('totalSupply does not exist.');
        }
        const totalSupply = parseInt(totalSupplyBytes.toString()) - amountInt;
        await ctx.stub.putState(totalSupplyKey, Buffer.from(totalSupply.toString()));

        // Emit the Transfer event
        const transferEvent = { from: minter, to: '0x0', value: amountInt };
        ctx.stub.setEvent('Transfer', Buffer.from(JSON.stringify(transferEvent)));

        console.log(`minter account ${minter} balance updated from ${currentBalance} to ${updatedBalance}`);
        return true;
    }

    /**
     * Returns the client ID of whoever calls the function
     * 
     * @param {Context} ctx the transaction context
     * @returns {Integer} client ID of caller
     */
    async ClientAccountID(ctx) {
        // Get ID of submitting client identity
        const clientAccountID = ctx.clientIdentity.getID();
        return clientAccountID;
    }

    /**
     * Registers a collaborator's good action in the blockchain and rewards them
     * 
     * @param {Context} ctx the transaction context
     * @param {String} from action owner
     * @param {String} to collaborator that fulfills the action
     * @param {Integer} actionID action of the fulfilled action
     * @param {Integer} value value of the action reward
     * @param {Integer} time time of the action fulfillment
     * @param {String} ipfsHash hash of the action proof image
     * @returns {boolean} result of the transaction
     */
    async processAction(ctx, from, to, actionID, value, time, ipfsHash) {
        // Check minter authorization - this sample assumes 'ud' is the central banker with privilege to mint new tokens
        const clientMSPID = ctx.clientIdentity.getMSPID();
        if (clientMSPID !== adminMSP) {
            throw new Error('client is not authorized to mint new tokens');
        }

        const from = ctx.clientIdentity.getID();

        const transferResp = await this._transfer(ctx, from, to, value);
        if (!transferResp) {
            throw new Error('Failed to transfer');
        }

        // Emit the Transfer event
        const actionEvent = { from, to, actionID, value: parseInt(value), time: parseInt(time), ipfsHash };
        ctx.stub.setEvent('Action', Buffer.from(JSON.stringify(actionEvent)));

        return true;
    }
}

module.exports = DeustocoinContract;