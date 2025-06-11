# Thinking steps

## Multi send transactions analysis

Analyzing some of the transaction of the multi send contract, I found that these are the 3 ways Safe is used to interact with other smart contracts:
- EOA sends a tx to a SafeProxy with execTransaction and the inner tx has to = target contract
- EOA sends a tx to a SafeProxy with execTransaction and the inner tx has to = multi send contract, the inner data is the tx list and each of them is directed to a target contract
- EOA sends a tx to the multi send contract, the data is the tx list and EVERY inner tx is directed to a SafeProxy with method = execTransaction, which will call a target contract

There is the possibility that in the last 2 points a recursive thing is present (i.e. in point 2 one of the tx in the list is directed to a multi send contract and in point 3 the execTransaction will have inner to = multi send contract), but it would make no sense to create such a tx to begin with as the EOA could just expand the initial list of transactions.

There is also the possibility that in the point 2 one of the tx in the list will be an execTransaction directed to a SafeProxy, I'll check that it's not happening during the run of the code to get the solution.

The point 3 could also have some tx in the list that are not execTransaction for a SafeProxy, those can be ignored because they are not making use of Safe, they are just random tx made on behalf of the EOA bundled togheter.

## No multi send

We already have the solution for the first point, we just run this query and remove the multi send contracts' addresses:

```
WITH result AS (
SELECT
  varbinary_substring(data, 17, 20) AS protocol_address,
  COUNT(*) AS tx_count
FROM ethereum.transactions
WHERE block_time > now() - interval '30' day
  AND varbinary_substring(data, 1, 4) = 0x6a761202 AND "to" IN (
    SELECT address FROM safe_ethereum.safes
  )
GROUP BY varbinary_substring(data, 17, 20)
ORDER BY COUNT(*) DESC
) SELECT cm.contract_project, r.protocol_address, r.tx_count
FROM result r JOIN contracts.contract_mapping cm
ON r.protocol_address = cm.contract_address
WHERE cm.blockchain = 'ethereum' ORDER BY r.tx_count DESC;
```

## EOA to multi send

This is the easiest of the last 2 points since we have a small number of "to" addresses (the multi send contracts) so we can easily run the calculation with a script (see case3.py). I just got a random one (example_tx.txt), splitted bytes visually to have them clearer and then implemented the script.

So here I found ~200 inner transactions that are not execTransaction. These are proxy creation followed by contract calls but NOT through the proxy created, should we consider those contracts in the count or not? For now I haven't included them. If we want them I just need to consider the "to" of the inner tx which is these case is not a SafeProxy but a target contract.

## execTransaction to multi send

This is the hardest case since we can't filter transactions with etherscan API. I can get the hashes of the txs sent from proxies from Dune like this:

```
select hash from ethereum.transactions WHERE block_time > now() - interval '30' day
  AND varbinary_substring(data, 1, 4) = 0x6a761202 AND "to" IN (
    SELECT address FROM safe_ethereum.safes
  ) AND varbinary_substring(data, 17, 20) = 0x40a2accbd92bca938b02010e17a5b8929b49130d;
```

but I can't export the addresses in csv and also it would take a lot of calls to etherscan anyway since they are more than 5k transactions in the last month. I could get all the tx data from Dune but I still can't export the csv.

The only idea that comes to mind is: using etherscan to get the logs with the topic0 `ExecutionSuccess(bytes32,uint256)`. I will probably get some other non-related stuff but the txs emitting these logs will not have the execTransaction method so I will just discard them. After I have all the hashes, I get all the txs from a node with RPC since I can batch the `eth_getTransactionByHash` calls inside the RPC request. Once I have all the txs I will run a script to extract the data in a similar way of the previous point, the example script is case2.py (not tested, just sketched).

## Results

So each point returns a top10, to get the real top ten precisely I should get the full list and add all the 3 cases togheter
