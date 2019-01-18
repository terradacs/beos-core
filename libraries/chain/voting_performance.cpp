#include <eosio/chain/voting_manager.hpp>

#include <eosio/chain/config.hpp>
#include <eosio/chain/controller.hpp>
#include <eosio/chain/database_utils.hpp>
#include <eosio/chain/exceptions.hpp>

#include <memory>

namespace eosio {
namespace chain {

producer_information::producer_information( const controller& c, const chainbase::database& d )
                     : _controller( c ), _db( d )
{

}

void producer_information::clear()
{
   gathered_producers.clear();
}

void producer_information::refresh()
{
   if( table_id )
      return;

   fc::microseconds abi_serializer_max_time{1000*25}; //25 ms

   abi = eosio::chain::table_helper::get_abi( _controller, config::system_account_name );
   abis = abi_serializer( abi, abi_serializer_max_time );

   const auto table_type = eosio::chain::table_helper::get_table_type(abi, N(producers));

   EOS_ASSERT(table_type == eosio::chain::table_helper::KEYi64, chain::contract_table_query_exception, "Invalid table type ${type} for table producers", ("type",table_type));

   table_id = _db.find< chain::table_id_object, chain::by_code_scope_table >(
         boost::make_tuple( config::system_account_name, config::system_account_name, N(producers) ) );
}

void producer_information::get_actual_producer( const account_name& acnt, producer_info_index::iterator& found )
{
   found = gathered_producers.find( acnt );

   if( found == gathered_producers.end() )
   {
      vector<char> data;
      static fc::microseconds abi_serializer_max_time{1000*25}; //25 ms

      refresh();

      if( table_id )
      {
         const auto& kv_index = _db.get_index<key_value_index, by_scope_primary>();

         auto itr = kv_index.find( boost::make_tuple( table_id->id, acnt ) );
         if( itr != kv_index.end() )
         {
            eosio::chain::table_helper::copy_inline_row( *itr, data );
            auto res = abis.binary_to_variant( "producer_info", data, abi_serializer_max_time, true/*shorten_abi_errors*/ );
            add_producer( res );

            found = gathered_producers.find( acnt );
         }
      }
   }
}

void producer_information::add_producer( const fc::variant& v )
{
   auto vo = v.get_object();
   auto owner = eosio::chain::string_to_name( vo["owner"].as<std::string>().c_str() );

   auto obj = std::make_shared< block_producer_voting_info >();

   obj->owner = owner;
   obj->total_votes = std::stod( vo["total_votes"].as<std::string>() );
   obj->is_active = vo["is_active"].as<bool>();

   gathered_producers.emplace( owner, obj );
}

std::vector<fc::variant> producer_information::get_producers( const fc::microseconds& abi_serializer_max_time )
{
   vector<fc::variant> result;
   vector<char> data;

   refresh();

   const auto& kv_index = _db.get_index<key_value_index, by_scope_primary>();

   /*
      'table_id' can be null. See 'bootseq_tests/bootseq_test'
   */
   if( table_id )
   {
      auto itr = kv_index.lower_bound( boost::make_tuple( table_id->id ) );
      while( itr != kv_index.end() && itr->t_id == table_id->id )
      {
         eosio::chain::table_helper::copy_inline_row( *itr, data);
         result.emplace_back( abis.binary_to_variant( "producer_info", data, abi_serializer_max_time, true/*shorten_abi_errors*/ ) );
         ++itr;
      }
   }

   return result;
}

std::vector<fc::variant> producer_information::get_producers( const fc::microseconds& abi_serializer_max_time, bool shorten_abi_errors, bool json, const std::string& lower_bound, uint32_t limit, double& total_producer_vote_weight, std::string& more )
{
   total_producer_vote_weight = 0;
   more = "";

   vector<fc::variant> result;
   vector<char> data;

   refresh();

   const auto& kv_index = _db.get_index<key_value_index, by_scope_primary>();

   const auto lower = name{lower_bound};
   static const uint8_t secondary_index_num = 0;

   const auto* const secondary_table_id = _db.find<chain::table_id_object, chain::by_code_scope_table>(
           boost::make_tuple(config::system_account_name, config::system_account_name, N(producers) | secondary_index_num));
   EOS_ASSERT(table_id && secondary_table_id, chain::contract_table_query_exception, "Missing producers table");

   const auto& secondary_index = _db.get_index<index_double_index>().indices();
   const auto& secondary_index_by_primary = secondary_index.get<by_primary>();
   const auto& secondary_index_by_secondary = secondary_index.get<by_secondary>();

   const auto stopTime = fc::time_point::now() + fc::microseconds(1000 * 10 ); // 10ms

   auto it = [&]{
      if(lower.value == 0)
         return secondary_index_by_secondary.lower_bound(
            boost::make_tuple(secondary_table_id->id, eosio::chain::table_helper::to_softfloat64(std::numeric_limits<double>::lowest()), 0));
      else
         return secondary_index.project<by_secondary>(
            secondary_index_by_primary.lower_bound(
               boost::make_tuple(secondary_table_id->id, lower.value)));
   }();

   for( ; it != secondary_index_by_secondary.end() && it->t_id == secondary_table_id->id; ++it ) {
      if ( result.size() >= limit || fc::time_point::now() > stopTime ) {
         more = name{it->primary_key}.to_string();
         break;
      }
      eosio::chain::table_helper::copy_inline_row(*kv_index.find(boost::make_tuple(table_id->id, it->primary_key)), data);
      if (json)
         result.emplace_back( abis.binary_to_variant( abis.get_table_type(N(producers)), data, abi_serializer_max_time, shorten_abi_errors ) );
      else
         result.emplace_back(fc::variant(data));
   }

   total_producer_vote_weight = eosio::chain::table_helper::get_global_row( _db, abi, abis, abi_serializer_max_time, shorten_abi_errors)["total_producer_vote_weight"].as_double();

   return result;
}

wasm_data_writer::res_pair wasm_data_writer::get( const account_name& owner )
{
   auto found = memory.find( owner );

   if( found == memory.end() )
   {
      aux::eosio_assert( idx < max, "incorrect pointer in WASM data");

      memory[ owner ] = idx;
      return res_pair( ptr + idx, true );
   }
   else
      return res_pair( ptr + memory[ owner ], false );
}

void wasm_data_writer::clear( block_producer_voting_info* _ptr, uint32_t _max )
{
   idx = 0;
   memory.clear();

   ptr = _ptr;
   max = _max;
}

void wasm_data_writer::save( const account_name& owner, double total_votes, bool is_active )
{
   aux::eosio_assert( ptr != nullptr && max > 0, "WASM data must exist");

   auto actual = get( owner );

   actual.first->owner = owner;
   actual.first->total_votes = total_votes;
   actual.first->is_active = is_active;

   if( actual.second )
      ++idx;
}

} } /// namespace eosio::chain

