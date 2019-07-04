#include <eosio.sudo/eosio.sudo.hpp>
#include <eosiolib/transaction.hpp>

namespace eosio {

/*
exec function manually parses input data (instead of taking parsed arguments from dispatcher)
because parsing data in the dispatcher uses too much CPU if the included transaction is very big

If we use dispatcher the function signature should be:

void sudo::exec( account_name executer,
                 transaction  trx )
*/

void sudo::exec() {
   require_auth( _self );

   size_t size = action_data_size();
   std::unique_ptr<char, decltype(&free)> buffer( reinterpret_cast<char*>( malloc( size ) ), &free );
   read_action_data( buffer.get(), size );

   account_name executer;

   datastream<const char*> ds( buffer.get(), size );
   ds >> executer;

   require_auth( executer );

   size_t trx_pos = ds.tellp();
   send_deferred( (uint128_t(executer) << 64) | current_time(), executer, buffer.get()+trx_pos, size-trx_pos );
}

} /// namespace eosio

EOSIO_ABI( eosio::sudo, (exec) )
