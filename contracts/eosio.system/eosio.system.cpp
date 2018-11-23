#include "eosio.system.hpp"
#include <eosiolib/dispatcher.hpp>

#include "producer_pay.cpp"
#include "delegate_bandwidth.cpp"
#include "voting.cpp"
#include "exchange_state.cpp"


namespace eosiosystem {

   system_contract::system_contract( account_name s )
   :immutable_system_contract(s),
    _global(_self,_self),
    _rammarket(_self,_self)
   {
      //print( "construct system\n" );
      if (_global.exists() == false)
         _gstate = get_default_parameters();
      else
      {
         _gstate = _global.get();
         _min_activated_stake = get_min_activated_stake();
      }

      flush_voting_stats();

      auto itr = _rammarket.find(S(4,RAMCORE));

      if( itr == _rammarket.end() ) {
         auto system_token_supply   = eosio::token(N(eosio.token)).get_supply(eosio::symbol_type(system_token_symbol).name()).amount;
         if( system_token_supply > 0 ) {
            itr = _rammarket.emplace( _self, [&]( auto& m ) {
               m.supply.amount = 100'000'000'000'000ll;
               m.supply.symbol = S(4,RAMCORE);
               m.base.balance.amount = int64_t(_gstate.free_ram());
               m.base.balance.symbol = S(0,RAM);
               m.quote.balance.amount = system_token_supply / 1000;
               m.quote.balance.symbol = CORE_SYMBOL;
            });
         }
      } else {
         //print( "ram market already created" );
      }
   }

   void system_contract::initialissue( uint64_t quantity, uint8_t min_activated_stake_percent )
     {
     require_auth( _self );

     asset balance = eosio::token(N(eosio.token)).check_balance( _self, CORE_SYMBOL );
     eosio_assert( balance.amount == 0, "call after any issue or second call is prohibited" );
     eosio_assert( quantity != 0, "quantity is non-positive value" );
     eosio_assert( 0 <= min_activated_stake_percent && min_activated_stake_percent <= 100, "min_activated_stake_percent must be in range [0:100]" );
     asset value( quantity, CORE_SYMBOL );
     std::string memo("initialissue");
     INLINE_ACTION_SENDER(eosio::token, issue)( N(eosio.token), { _self, N(active) }, { _self, value, memo } );
     // min_activated_stake_percent % of quantity
     _min_activated_stake = static_cast<int64_t>( static_cast<int128_t>(quantity) * min_activated_stake_percent / 100 );
     set_min_activated_stake( _min_activated_stake );
     }

   eosio_global_state system_contract::get_default_parameters() {
      eosio_global_state dp;
      get_blockchain_parameters(dp);
      return dp;
   }


   system_contract::~system_contract() {
      //print( "destruct system\n" );
      _global.set(_gstate, _self);
      //eosio_exit(0);
      }

   void system_contract::setram( uint64_t max_ram_size ) {
      require_auth( _self );

      eosio_assert( _gstate.max_ram_size < max_ram_size, "ram may only be increased" ); /// decreasing ram might result market maker issues
      eosio_assert( max_ram_size < 1024ll*1024*1024*1024*1024, "ram size is unrealistic" );
      eosio_assert( max_ram_size > _gstate.total_ram_bytes_reserved, "attempt to set max below reserved" );

      auto delta = int64_t(max_ram_size) - int64_t(_gstate.max_ram_size);
      auto itr = _rammarket.find(S(4,RAMCORE));

      /**
       *  Increase or decrease the amount of ram for sale based upon the change in max
       *  ram size.
       */
      _rammarket.modify( itr, 0, [&]( auto& m ) {
         m.base.balance.amount += delta;
      });

      _gstate.max_ram_size = max_ram_size;
      _global.set( _gstate, _self );
   }

   void system_contract::setparams( const eosio::blockchain_parameters& params ) {
      require_auth( N(eosio) );
      (eosio::blockchain_parameters&)(_gstate) = params;
      eosio_assert( 3 <= _gstate.max_authority_depth, "max_authority_depth should be at least 3" );
      set_blockchain_parameters( params );
   }

   void system_contract::setpriv( account_name account, uint8_t ispriv ) {
      require_auth( _self );
      set_privileged( account, ispriv );
   }

   void system_contract::rmvproducer( account_name producer ) {
      require_auth( _self );
      auto prod = _producers.find( producer );
      eosio_assert( prod != _producers.end(), "producer not found" );
      _producers.modify( prod, 0, [&](auto& p) {
            p.deactivate();
         });
   }

   void system_contract::bidname( account_name bidder, account_name newname, asset bid ) {
      require_auth( bidder );
      eosio_assert( eosio::name_suffix(newname) == newname, "you can only bid on top-level suffix" );
      eosio_assert( newname != 0, "the empty name is not a valid account name to bid on" );
      eosio_assert( (newname & 0xFull) == 0, "13 character names are not valid account names to bid on" );
      eosio_assert( (newname & 0x1F0ull) == 0, "accounts with 12 character names and no dots can be created without bidding required" );
      eosio_assert( !is_account( newname ), "account already exists" );
      eosio_assert( bid.symbol == asset().symbol, "asset must be system token" );
      eosio_assert( bid.amount > 0, "insufficient bid" );

      INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {bidder,N(active)},
                                                    { bidder, N(eosio.names), bid, std::string("bid name ")+(name{newname}).to_string()  } );

      name_bid_table bids(_self,_self);
      print( name{bidder}, " bid ", bid, " on ", name{newname}, "\n" );
      auto current = bids.find( newname );
      if( current == bids.end() ) {
         bids.emplace( bidder, [&]( auto& b ) {
            b.newname = newname;
            b.high_bidder = bidder;
            b.high_bid = bid.amount;
            b.last_bid_time = current_time();
         });
      } else {
         eosio_assert( current->high_bid > 0, "this auction has already closed" );
         eosio_assert( bid.amount - current->high_bid > (current->high_bid / 10), "must increase bid by 10%" );
         eosio_assert( current->high_bidder != bidder, "account is already highest bidder" );

         INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {N(eosio.names),N(active)},
                                                       { N(eosio.names), current->high_bidder, asset(current->high_bid),
                                                       std::string("refund bid on name ")+(name{newname}).to_string()  } );

         bids.modify( current, bidder, [&]( auto& b ) {
            b.high_bidder = bidder;
            b.high_bid = bid.amount;
            b.last_bid_time = current_time();
         });
      }
   }

  void system_contract::reward( account_name receiver, int64_t ram_bytes, asset net_weight, asset cpu_weight )
  {
     change_resource_limits( receiver, ram_bytes, net_weight.amount, cpu_weight.amount );
  }

   /**
    *  Called after a new account is created. This code enforces resource-limits rules
    *  for new accounts as well as new account naming conventions.
    *
    *  Account names containing '.' symbols must have a suffix equal to the name of the creator.
    *  This allows users who buy a premium name (shorter than 12 characters with no dots) to be the only ones
    *  who can create accounts with the creator's name as a suffix.
    *
    */
   void native::newaccount( account_name     creator,
                            account_name     newact,
                            bool init_ram
                            /*const authority& owner,
                            const authority& active*/ ) {

      if( creator != N(beos.gateway) && creator != _self ) {
         auto tmp = newact >> 4;
         bool has_dot = false;

         for( uint32_t i = 0; i < 12; ++i ) {
           has_dot |= !(tmp & 0x1f);
           tmp >>= 5;
         }
         if( has_dot ) { // or is less than 12 characters
            auto suffix = eosio::name_suffix(newact);
            if( suffix == newact ) {
               name_bid_table bids(_self,_self);
               auto current = bids.find( newact );
               eosio_assert( current != bids.end(), "no active bid for name" );
               eosio_assert( current->high_bidder == creator, "only highest bidder can claim" );
               eosio_assert( current->high_bid < 0, "auction for name is not closed yet" );
               bids.erase( current );
            } else {
               eosio_assert( creator == suffix, "only suffix may create this account" );
            }
         }
      }

    int64_t bytes = 0;
    if( init_ram ) {
       bytes = get_account_ram_usage( newact );
       /*
        Basic RAM usage = 2724 bytes

        Unfortunately, this is not enough for making transfer, as result is an exception:
        'account has insufficient ram; needs 2852 bytes has 2724 bytes'

        Solution: increasing RAM
       */
       bytes *= 2;
       change_resource_limits( creator, -bytes, 0, 0 );
    }

    set_resource_limits( newact, bytes, 0, 0 );
   }

   void system_contract::flush_voting_stats()
      {
      get_voting_stats(&_gstate.total_activated_stake, &_gstate.thresh_activated_stake_time,
         &_gstate.total_producer_vote_weight);

      /// Save just updated _gstate to the global table.
      _global.set(_gstate, _self);
      }

} /// eosiosystem


EOSIO_ABI( eosiosystem::system_contract,
     // native.hpp (newaccount definition is actually in eosio.system.cpp)
     (initresource)(reward)(newaccount)(updateauth)(deleteauth)(linkauth)(unlinkauth)(canceldelay)(onerror)
     // eosio.system.cpp
     (initialissue)(setram)(setparams)(setpriv)(rmvproducer)(bidname)
     // delegate_bandwidth.cpp
     (buyrambytes)(buyram)(sellram)(delegatebw)(undelegatebw)(refund)
     // voting.cpp
     (regproducer)(unregprod)(voteproducer)(regproxy)
     // producer_pay.cpp
     (onblock)(claimrewards)
)
