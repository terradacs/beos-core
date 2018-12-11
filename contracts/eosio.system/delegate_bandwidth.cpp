/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#include "eosio.system.hpp"

#include <eosiolib/eosio.hpp>
#include <eosiolib/print.hpp>
#include <eosiolib/datastream.hpp>
#include <eosiolib/serialize.hpp>
#include <eosiolib/multi_index.hpp>
#include <eosiolib/privileged.h>
#include <eosiolib/transaction.hpp>

#include <eosio.token/eosio.token.hpp>

#include <eosio.distribution/eosio.distribution.hpp>
#include <beoslib/beos_privileged.hpp>

#include <cmath>
#include <map>

namespace eosiosystem {
   using eosio::asset;
   using eosio::indexed_by;
   using eosio::const_mem_fun;
   using eosio::bytes;
   using eosio::print;
   using eosio::permission_level;
   using std::map;
   using std::pair;

   static constexpr beos_time refund_delay = 3*24*3600;
   static constexpr beos_time refund_expiration_time = 3600;

   struct user_resources {
      account_name  owner;
      asset         net_weight;
      asset         cpu_weight;
      int64_t       ram_bytes = 0;

      uint64_t primary_key()const { return owner; }

      // explicit serialization macro is not necessary, used here only to improve compilation time
      EOSLIB_SERIALIZE( user_resources, (owner)(net_weight)(cpu_weight)(ram_bytes) )
   };

   /**
    *  Every user 'from' has a scope/table that uses every receipient 'to' as the primary key.
    */
   struct delegated_bandwidth {
      account_name  from;
      account_name  to;
      asset         net_weight;
      asset         cpu_weight;

      uint64_t  primary_key()const { return to; }

      // explicit serialization macro is not necessary, used here only to improve compilation time
      EOSLIB_SERIALIZE( delegated_bandwidth, (from)(to)(net_weight)(cpu_weight) )

   };

   struct refund_request {
      account_name  owner;
      beos_time     request_time;
      eosio::asset  net_amount;
      eosio::asset  cpu_amount;

      uint64_t  primary_key()const { return owner; }

      // explicit serialization macro is not necessary, used here only to improve compilation time
      EOSLIB_SERIALIZE( refund_request, (owner)(request_time)(net_amount)(cpu_amount) )
   };

   /**
    *  These tables are designed to be constructed in the scope of the relevant user, this
    *  facilitates simpler API for per-user queries
    */
   typedef eosio::multi_index< N(delband), delegated_bandwidth> del_bandwidth_table;
   typedef eosio::multi_index< N(refunds), refund_request>      refunds_table;

   bool system_contract::is_allowed_ram_operation() const {
      //RAM shouldn't be liquid during distribution period.
      return eosio::distribution( N(beos.distrib) ).is_past_ram_distribution_period();
   }

   /**
    *  This action will buy an exact amount of ram and bill the payer the current market price.
    */
   void system_contract::buyrambytes( account_name payer, account_name receiver, uint32_t bytes ) {

      eosio_assert( is_allowed_ram_operation(), "RAM shouldn't be liquid during distribution period" );

      auto itr = _rammarket.find(S(4,RAMCORE));
      auto tmp = *itr;
      auto ram_cost = - tmp.convert( -asset(bytes,S(0,RAM)), CORE_SYMBOL, true );
      ram_cost.amount = (200 * ram_cost.amount + 199) / 199;

      /*
      auto eosout = tmp.convert( asset(bytes,S(0,RAM)), CORE_SYMBOL );
      ABW: the original formula above is incorrect:
       - it does not take fee into account
       - it wrongfully assumes that if we could sell 'bytes' of RAM at current market for 'eosout' we could also
         buy the same amount for that price; the difference grows the bigger chunk of current market we want to buy
      Corrected formula is much closer regardless of market parameters and actually overestimates slightly (it is
      not possible to get exact value due to limits in CORE_SYMBOL precision).
      
      auto tmp2 = *itr;
      auto wrong_ram_cost = tmp2.convert( asset(bytes,S(0,RAM)), CORE_SYMBOL );
      auto wrong_fee = wrong_ram_cost;
      wrong_fee.amount = ( wrong_fee.amount + 199 ) / 200;
      wrong_ram_cost.amount -= wrong_fee.amount;
      auto tmp3 = *itr;
      int64_t wrong_bytes_out = tmp3.convert( wrong_ram_cost, S(0,RAM) ).amount;
      auto fee = ram_cost;
      fee.amount = ( fee.amount + 199 ) / 200;
      auto good_ram_cost = ram_cost;
      good_ram_cost.amount -= fee.amount;
      auto tmp4 = *itr;
      int64_t bytes_out = tmp4.convert( good_ram_cost, S(0,RAM) ).amount;
      eosio::print( "\nasked for RAM: ", bytes );
      eosio::print( "\nwrong RAM cost: ", wrong_ram_cost, " + ", wrong_fee, "; gives RAM: ", wrong_bytes_out );
      eosio::print( "\nbetter RAM cost: ", good_ram_cost, " + ", fee, "; gives RAM: ", bytes_out );
      eosio::print( "\nwrong is short by ", bytes-wrong_bytes_out, "\nbetter is over by ", bytes_out-bytes, "\n" );
      //*/

      buyram( payer, receiver, ram_cost );
   }


   /**
    *  When buying ram the payer irreversiblly transfers quant to system contract and only
    *  the receiver may reclaim the tokens via the sellram action. The receiver pays for the
    *  storage of all database records associated with this action.
    *
    *  RAM is a scarce resource whose supply is defined by global properties max_ram_size. RAM is
    *  priced using the bancor algorithm such that price-per-byte with a constant reserve ratio of 100:1.
    */
   void system_contract::buyram( account_name payer, account_name receiver, asset quant )
   {
      eosio_assert( is_allowed_ram_operation(), "RAM shouldn't be liquid during distribution period" );

      require_auth( payer );
      eosio_assert( quant.amount > 0, "must purchase a positive amount" );

      auto fee = quant;
      fee.amount = ( fee.amount + 199 ) / 200; /// .5% fee (round up)
      // fee.amount cannot be 0 since that is only possible if quant.amount is 0 which is not allowed by the assert above.
      // If quant.amount == 1, then fee.amount == 1,
      // otherwise if quant.amount > 1, then 0 < fee.amount < quant.amount.
      auto quant_after_fee = quant;
      quant_after_fee.amount -= fee.amount;
      // quant_after_fee.amount should be > 0 if quant.amount > 1.
      // If quant.amount == 1, then quant_after_fee.amount == 0 and the next inline transfer will fail causing the buyram action to fail.

      INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {payer,N(active)},
         { payer, N(eosio.ram), quant_after_fee, std::string("buy ram") } );

      if( fee.amount > 0 ) {
         INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {payer,N(active)},
                                                       { payer, N(eosio.ramfee), fee, std::string("ram fee") } );
      }

      int64_t bytes_out;

      const auto& market = _rammarket.get(S(4,RAMCORE), "ram market does not exist");
      _rammarket.modify( market, 0, [&]( auto& es ) {
          bytes_out = es.convert( quant_after_fee,  S(0,RAM) ).amount;
      });

      eosio_assert( bytes_out > 0, "must reserve a positive amount" );

      _gstate.total_ram_bytes_reserved += uint64_t(bytes_out);
      _gstate.total_ram_stake          += quant_after_fee.amount;

      change_resource_limits( receiver, bytes_out, 0, 0 );
   }

   void system_contract::initresource( account_name receiver, int64_t bytes, int64_t stake_net_quantity, int64_t stake_cpu_quantity )
   {
      require_auth( _self );
      int64_t _ram_bytes, _net_weight, _cpu_weight;
      get_resource_limits( receiver, &_ram_bytes, &_net_weight, &_cpu_weight );
      eosio_assert( (bytes < 0 || _ram_bytes < 0) &&
                    (stake_net_quantity < 0 || _net_weight < 0) &&
                    (stake_cpu_quantity < 0 || _cpu_weight < 0),
                    "can only be called to replace lack of limit with concrete resource value" );
    
      // replicate buyrambytes but without a fee (but buy a bit more - it is better to buy more and claim we bought less, so ram
      // market is never short, than to do the opposite, especially that ram market itself claims to have funds it doesn't have)
      if ( bytes == 0 ) {
         _ram_bytes = bytes;
      } else if ( bytes > 0 ) {
         auto itr = _rammarket.find(S(4,RAMCORE));
         eosio_assert( itr != _rammarket.end(), "ram market does not exist");
         auto tmp = *itr;
         auto bytes_extra = bytes * 100001 / 100000;
         auto ram_cost = - tmp.convert( -asset(bytes_extra,S(0,RAM)), CORE_SYMBOL, true );

         INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {_self,N(active)},
            { _self, N(eosio.ram), ram_cost, std::string("buy ram") } );

         int64_t bytes_out;
         _rammarket.modify( *itr, 0, [&]( auto& es ) {
            bytes_out = es.convert( ram_cost, S(0,RAM) ).amount;
         });
         eosio_assert( bytes_out >= bytes, "failed ram cost estimation formula" );
         eosio_assert( (bytes - bytes_out)*1000 / bytes == 0, "failed ram cost estimation formula" );

         _gstate.total_ram_bytes_reserved += uint64_t(bytes);
         _gstate.total_ram_stake          += ram_cost.amount;
         _ram_bytes = bytes;
      }

      // replicate delegatebw but without votes and record for undelegate
      int64_t transfer_amount = 0;
      if ( stake_net_quantity >= 0 ) {
         _net_weight = stake_net_quantity;
         transfer_amount += stake_net_quantity;
      }
      if ( stake_cpu_quantity >= 0 ) {
         _cpu_weight = stake_cpu_quantity;
         transfer_amount += stake_cpu_quantity;
      }
      if ( transfer_amount > 0 ) {
         INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {_self, N(active)},
            { _self, N(eosio.stake), asset(transfer_amount), std::string("stake bandwidth") } );
      }

      set_resource_limits( receiver, _ram_bytes, _net_weight, _cpu_weight );
   }

   /**
    *  The system contract now buys and sells RAM allocations at prevailing market prices.
    *  This may result in traders buying RAM today in anticipation of potential shortages
    *  tomorrow. Overall this will result in the market balancing the supply and demand
    *  for RAM over time.
    */
   void system_contract::sellram( account_name account, int64_t bytes ) {

      eosio_assert( is_allowed_ram_operation(), "RAM shouldn't be liquid during distribution period" );

      require_auth( account );
      eosio_assert( bytes > 0, "cannot sell negative byte" );

      asset tokens_out;
      auto itr = _rammarket.find(S(4,RAMCORE));
      _rammarket.modify( itr, 0, [&]( auto& es ) {
          /// the cast to int64_t of bytes is safe because we certify bytes is <= quota which is limited by prior purchases
          tokens_out = es.convert( asset(bytes,S(0,RAM)), CORE_SYMBOL);
      });

      eosio_assert( tokens_out.amount > 1, "token amount received from selling ram is too low" );

      _gstate.total_ram_bytes_reserved -= static_cast<decltype(_gstate.total_ram_bytes_reserved)>(bytes); // bytes > 0 is asserted above
      _gstate.total_ram_stake          -= tokens_out.amount;

      //// this shouldn't happen, but just in case it does we should prevent it
      eosio_assert( _gstate.total_ram_stake >= 0, "error, attempt to unstake more tokens than previously staked" );

      change_resource_limits( account, -bytes, 0, 0 );

      INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {N(eosio.ram),N(active)},
                                                       { N(eosio.ram), account, asset(tokens_out), std::string("sell ram") } );

      auto fee = ( tokens_out.amount + 199 ) / 200; /// .5% fee (round up)
      // since tokens_out.amount was asserted to be at least 2 earlier, fee.amount < tokens_out.amount
      
      if( fee > 0 ) {
         INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {account,N(active)},
            { account, N(eosio.ramfee), asset(fee), std::string("sell ram fee") } );
      }
   }

   void system_contract::changebw( account_name from, account_name receiver,
                                   const asset stake_net_delta, const asset stake_cpu_delta, bool transfer )
   {
      require_auth( from );
      eosio_assert( stake_net_delta != asset(0) || stake_cpu_delta != asset(0), "should stake non-zero amount" );
      eosio_assert( std::abs( (stake_net_delta + stake_cpu_delta).amount )
                     >= std::max( std::abs( stake_net_delta.amount ), std::abs( stake_cpu_delta.amount ) ),
                    "net and cpu deltas cannot be opposite signs" );

      account_name source_stake_from = from;
      if ( transfer ) {
         from = receiver;
      }

      // update stake delegated from "from" to "receiver"
      {
         del_bandwidth_table     del_tbl( _self, from);
         auto itr = del_tbl.find( receiver );
         if( itr == del_tbl.end() ) {

            auto _stake_net_delta = stake_net_delta;
            auto _stake_cpu_delta = stake_cpu_delta;

            if( from == receiver )
            {
              int64_t _ram_bytes, _net_weight, _cpu_weight;
              get_distribution_resource_rewards( from, &_ram_bytes, &_net_weight, &_cpu_weight );
              if( _ram_bytes > 0 || _net_weight > 0 || _cpu_weight > 0 )
                enable_unstake_mode_distribution_resource_rewards( from );

              _stake_net_delta.amount += _net_weight;
              _stake_cpu_delta.amount += _cpu_weight;
            }

            itr = del_tbl.emplace( from, [&]( auto& dbo ){
                  dbo.from          = from;
                  dbo.to            = receiver;
                  dbo.net_weight    = _stake_net_delta;
                  dbo.cpu_weight    = _stake_cpu_delta;
               });
         }
         else {
            del_tbl.modify( itr, 0, [&]( auto& dbo ){
                  dbo.net_weight    += stake_net_delta;
                  dbo.cpu_weight    += stake_cpu_delta;
               });
         }
         eosio_assert( asset(0) <= itr->net_weight, "insufficient staked net bandwidth" );
         eosio_assert( asset(0) <= itr->cpu_weight, "insufficient staked cpu bandwidth" );
         if ( itr->net_weight == asset(0) && itr->cpu_weight == asset(0) ) {
            del_tbl.erase( itr );
         }
      } // itr can be invalid, should go out of scope

      // update totals of "receiver"
      change_resource_limits( receiver, 0, stake_net_delta.amount, stake_cpu_delta.amount );

      // create refund or update from existing refund
      if ( N(eosio.stake) != source_stake_from ) { //for eosio both transfer and refund make no sense
         refunds_table refunds_tbl( _self, from );
         auto req = refunds_tbl.find( from );

         //create/update/delete refund
         auto net_balance = stake_net_delta;
         auto cpu_balance = stake_cpu_delta;
         bool need_deferred_trx = false;


         // net and cpu are same sign by assertions in delegatebw and undelegatebw
         // redundant assertion also at start of changebw to protect against misuse of changebw
         bool is_undelegating = (net_balance.amount + cpu_balance.amount ) < 0;
         bool is_delegating_to_self = (!transfer && from == receiver);

         if( is_delegating_to_self || is_undelegating ) {
            if ( req != refunds_tbl.end() ) { //need to update refund
               refunds_tbl.modify( req, 0, [&]( refund_request& r ) {
                  if ( net_balance < asset(0) || cpu_balance < asset(0) ) {
                     r.request_time = now();
                  }
                  r.net_amount -= net_balance;
                  if ( r.net_amount < asset(0) ) {
                     net_balance = -r.net_amount;
                     r.net_amount = asset(0);
                  } else {
                     net_balance = asset(0);
                  }
                  r.cpu_amount -= cpu_balance;
                  if ( r.cpu_amount < asset(0) ){
                     cpu_balance = -r.cpu_amount;
                     r.cpu_amount = asset(0);
                  } else {
                     cpu_balance = asset(0);
                  }
               });

               eosio_assert( asset(0) <= req->net_amount, "negative net refund amount" ); //should never happen
               eosio_assert( asset(0) <= req->cpu_amount, "negative cpu refund amount" ); //should never happen

               if ( req->net_amount == asset(0) && req->cpu_amount == asset(0) ) {
                  refunds_tbl.erase( req );
                  need_deferred_trx = false;
               } else {
                  need_deferred_trx = true;
               }

            } else if ( net_balance < asset(0) || cpu_balance < asset(0) ) { //need to create refund
               refunds_tbl.emplace( from, [&]( refund_request& r ) {
                  r.owner = from;
                  if ( net_balance < asset(0) ) {
                     r.net_amount = -net_balance;
                     net_balance = asset(0);
                  } // else r.net_amount = 0 by default constructor
                  if ( cpu_balance < asset(0) ) {
                     r.cpu_amount = -cpu_balance;
                     cpu_balance = asset(0);
                  } // else r.cpu_amount = 0 by default constructor
                  r.request_time = now();
               });
               need_deferred_trx = true;
            } // else stake increase requested with no existing row in refunds_tbl -> nothing to do with refunds_tbl
         } /// end if is_delegating_to_self || is_undelegating

         if ( need_deferred_trx ) {
            eosio::transaction out;
            out.actions.emplace_back( permission_level{ from, N(active) }, _self, N(refund), from );
            out.delay_sec = refund_delay;
            cancel_deferred( from ); // TODO: Remove this line when replacing deferred trxs is fixed
            out.send( from, from, true );
         } else {
            cancel_deferred( from );
         }

         auto transfer_amount = net_balance + cpu_balance;
         if ( asset(0) < transfer_amount ) {
            INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {source_stake_from, N(active)},
               { source_stake_from, N(eosio.stake), asset(transfer_amount), std::string("stake bandwidth") } );
         }
      }

      // update voting power
      asset total_update = stake_net_delta + stake_cpu_delta;
      update_voting_power(from, total_update.amount);
   }

   void system_contract::delegatebw( account_name from, account_name receiver,
                                     asset stake_net_quantity,
                                     asset stake_cpu_quantity, bool transfer )
   {
      eosio_assert( stake_cpu_quantity >= asset(0), "must stake a positive amount" );
      eosio_assert( stake_net_quantity >= asset(0), "must stake a positive amount" );
      eosio_assert( stake_net_quantity + stake_cpu_quantity > asset(0), "must stake a positive amount" );
      eosio_assert( !transfer || from != receiver, "cannot use transfer flag if delegating to self" );

      changebw( from, receiver, stake_net_quantity, stake_cpu_quantity, transfer);
   } // delegatebw

   void system_contract::undelegatebw( account_name from, account_name receiver,
                                       asset unstake_net_quantity, asset unstake_cpu_quantity )
   {
      eosio_assert( eosio::distribution( N(beos.distrib) ).is_past_beos_distribution_period(), "cannot unstake during distribution period" );
      eosio_assert( asset() <= unstake_cpu_quantity, "must unstake a positive amount" );
      eosio_assert( asset() <= unstake_net_quantity, "must unstake a positive amount" );
      eosio_assert( asset() < unstake_cpu_quantity + unstake_net_quantity, "must unstake a positive amount" );
      if ( _gstate.total_activated_stake < _min_activated_stake ) {
         std::string msg( "cannot undelegate bandwidth until the chain is activated (at least " );
         msg += std::to_string(_min_activated_stake_percent);
         msg += "% of all tokens participate in voting)";

         eosio_assert( false, msg.c_str() );
      }

      changebw( from, receiver, -unstake_net_quantity, -unstake_cpu_quantity, false);
   } // undelegatebw


   void system_contract::refund( const account_name owner ) {
      require_auth( owner );

      refunds_table refunds_tbl( _self, owner );
      auto req = refunds_tbl.find( owner );
      eosio_assert( req != refunds_tbl.end(), "refund request not found" );
      eosio_assert( req->request_time + refund_delay <= now(), "refund is not available yet" );
      // Until now() becomes NOW, the fact that now() is the timestamp of the previous block could in theory
      // allow people to get their tokens earlier than the 3 day delay if the unstake happened immediately after many
      // consecutive missed blocks.

      INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {N(eosio.stake),N(active)},
                                                    { N(eosio.stake), req->owner, req->net_amount + req->cpu_amount, std::string("unstake") } );

      refunds_tbl.erase( req );
   }


} //namespace eosiosystem
