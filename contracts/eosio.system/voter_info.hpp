/**
*  @file voter_info.hpp
*  @copyright defined in eos/LICENSE.txt
*/

#pragma once

#include <eosiolib/asset.hpp>
#include <eosiolib/serialize.hpp>
#include <eosiolib/types.h>

#include <vector>

namespace eosiosystem {

/** Holds all data related to voting specific to given `owner` account.
    Structure is shared between eosio.system and chain native code.
*/
struct voter_info {
   account_name                owner = 0; /// the voter
   account_name                proxy = 0; /// the proxy set by the voter, if any
   std::vector<account_name>   producers; /// the producers approved by this voter if no proxy set
   int64_t                     staked = 0;

   /**
   *  Every time a vote is cast we must first "undo" the last vote weight, before casting the
   *  new vote weight.  Vote weight is calculated as:
   *
   *  stated.amount * 2 ^ ( weeks_since_launch/weeks_per_year)
   */
   double                      last_vote_weight = 0; /// the vote weight cast the last time the vote was updated

                                                     /**
                                                     * Total vote weight delegated to this voter.
                                                     */
   double                      proxied_vote_weight = 0; /// the total vote weight delegated to this voter as a proxy
   bool                        is_proxy = 0; /// whether the voter is a proxy for others


   uint32_t                    reserved1 = 0;
   beos_time                   reserved2 = 0;
   eosio::asset                reserved3;

   uint64_t primary_key()const { return owner; }

   // explicit serialization macro is not necessary, used here only to improve compilation time
   EOSLIB_SERIALIZE(voter_info, (owner)(proxy)(producers)(staked)(last_vote_weight)(proxied_vote_weight)(is_proxy)(reserved1)(reserved2)(reserved3))
   };

} /// eosiosystem

