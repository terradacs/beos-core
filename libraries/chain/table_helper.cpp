#include <eosio/chain/table_helper.hpp>
#include <eosio/chain/controller.hpp>

namespace eosio {
namespace chain {

const std::string table_helper::KEYi64 = "i64";

abi_def table_helper::get_abi( const controller& db, const name& account )
{
   const auto &d = db.db();
   const account_object *code_accnt = d.find<account_object, by_name>(account);
   EOS_ASSERT(code_accnt != nullptr, chain::account_query_exception, "Fail to retrieve account for ${account}", ("account", account) );
   abi_def abi;
   abi_serializer::to_abi(code_accnt->abi, abi);
   return abi;
}

std::string table_helper::get_table_type( const abi_def& abi, const name& table_name ) {
   for( const auto& t : abi.tables ) {
      if( t.name == table_name ){
         return t.index_type;
      }
   }
   EOS_ASSERT( false, chain::contract_table_query_exception, "Table ${table} is not specified in the ABI", ("table",table_name) );
}

// TODO: move this and similar functions to a header. Copied from wasm_interface.cpp.
// TODO: fix strict aliasing violation
float64_t table_helper::to_softfloat64( double d )
{
   return *reinterpret_cast<float64_t*>(&d);
}

void table_helper::copy_inline_row(const chain::key_value_object& obj, vector<char>& data)
{
   data.resize( obj.value.size() );
   memcpy( data.data(), obj.value.data(), obj.value.size() );
}

fc::variant table_helper::get_global_row( const chainbase::database& db, const abi_def& abi, const abi_serializer& abis, const fc::microseconds& abi_serializer_max_time_ms, bool shorten_abi_errors )
{
   const auto table_type = eosio::chain::table_helper::get_table_type(abi, N(global));
   EOS_ASSERT(table_type == eosio::chain::table_helper::KEYi64, chain::contract_table_query_exception, "Invalid table type ${type} for table global", ("type",table_type));

   const auto* const table_id = db.find<chain::table_id_object, chain::by_code_scope_table>(boost::make_tuple(config::system_account_name, config::system_account_name, N(global)));
   EOS_ASSERT(table_id, chain::contract_table_query_exception, "Missing table global");

   const auto& kv_index = db.get_index<key_value_index, by_scope_primary>();
   const auto it = kv_index.find(boost::make_tuple(table_id->id, N(global)));
   EOS_ASSERT(it != kv_index.end(), chain::contract_table_query_exception, "Missing row in table global");

   vector<char> data;
   copy_inline_row(*it, data);
   return abis.binary_to_variant(abis.get_table_type(N(global)), data, abi_serializer_max_time_ms, shorten_abi_errors );
}

} } /// namespace eosio::chain

