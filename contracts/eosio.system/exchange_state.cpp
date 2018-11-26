#include <eosio.system/exchange_state.hpp>

namespace eosiosystem {
   asset exchange_state::convert_to_exchange( connector& c, asset in, bool cost_estimation ) {

      real_type R(supply.amount);
      real_type C(c.balance.amount+in.amount);
      real_type F(c.weight/1000.0);
      real_type T(in.amount);
      real_type ONE(1.0);

      real_type E = -R * (ONE - std::pow( ONE + T / C, F) );
      //print( "E: ", E, "\n");
      int64_t issued = cost_estimation ? (E < 0 ? int64_t(std::floor(E)) : int64_t(std::ceil(E))) : int64_t(E);

      supply.amount += issued;
      c.balance.amount += in.amount;

      return asset( issued, supply.symbol );
   }

   asset exchange_state::convert_from_exchange( connector& c, asset in, bool cost_estimation ) {
      eosio_assert( in.symbol== supply.symbol, "unexpected asset symbol input" );

      real_type R(supply.amount - in.amount);
      real_type C(c.balance.amount);
      real_type F(1000.0/c.weight);
      real_type E(in.amount);
      real_type ONE(1.0);


     // potentially more accurate: 
     // The functions std::expm1 and std::log1p are useful for financial calculations, for example, 
     // when calculating small daily interest rates: (1+x)n
     // -1 can be expressed as std::expm1(n * std::log1p(x)). 
     // real_type T = C * std::expm1( F * std::log1p(E/R) );
      
      real_type T = C * (std::pow( ONE + E/R, F) - ONE);
      //print( "T: ", T, "\n");
      int64_t out = cost_estimation ? (T < 0 ? int64_t(std::floor(T)) : int64_t(std::ceil(T))) : int64_t(T);

      supply.amount -= in.amount;
      c.balance.amount -= out;

      return asset( out, c.balance.symbol );
   }

   asset exchange_state::convert( asset from, symbol_type to, bool cost_estimation ) {
      auto sell_symbol  = from.symbol;
      auto ex_symbol    = supply.symbol;
      auto base_symbol  = base.balance.symbol;
      auto quote_symbol = quote.balance.symbol;

      //print( "From: ", from, " TO ", asset( 0,to), "\n" );
      //print( "base: ", base_symbol, "\n" );
      //print( "quote: ", quote_symbol, "\n" );
      //print( "ex: ", supply.symbol, "\n" );

      if( sell_symbol != ex_symbol ) {
         if( sell_symbol == base_symbol ) {
            from = convert_to_exchange( base, from, cost_estimation );
         } else if( sell_symbol == quote_symbol ) {
            from = convert_to_exchange( quote, from, cost_estimation );
         } else { 
            eosio_assert( false, "invalid sell" );
         }
      } else {
         if( to == base_symbol ) {
            from = convert_from_exchange( base, from, cost_estimation );
         } else if( to == quote_symbol ) {
            from = convert_from_exchange( quote, from, cost_estimation );
         } else {
            eosio_assert( false, "invalid conversion" );
         }
      }

      if( to != from.symbol )
         return convert( from, to, cost_estimation );

      return from;
   }



} /// namespace eosiosystem
