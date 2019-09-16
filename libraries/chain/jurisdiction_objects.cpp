
#include <eosio/chain/jurisdiction_objects.hpp>
#include <fc/variant_object.hpp>

namespace eosio { namespace chain {

std::string message::incorrect_location_in_transaction = "Transaction will be deferred due to the jurisdictions";

/*=============================trx_extensions_visitor=============================*/

trx_extensions_visitor::trx_extensions_visitor( const std::vector< char>& buffer )
                        : _buffer( buffer )
{
}

void trx_extensions_visitor::operator()( const jurisdiction_basic& _jurisdiction ) const
{
   jurisdiction = fc::raw::unpack< jurisdiction_basic >( _buffer );
}

/*=============================jurisdiction_provider_interface=============================*/

jurisdiction_provider_interface::ptr_base jurisdiction_provider_interface::getptr()
{
   return shared_from_this();
}

/*=============================jurisdiction_base_provider=============================*/

void jurisdiction_base_provider::update( const account_name& new_producer, size_t _producers_on_node )
{
   active_producer = new_producer;
   producers_on_node = _producers_on_node;
}

fc::optional< jurisdiction_producer > jurisdiction_base_provider::get_jurisdiction_producer()
{
   if( was_change && accounts.find( active_producer ) == accounts.end() && accounts.size() < producers_on_node )
      return jurisdiction_producer( active_producer, data.jurisdictions );
   else
      return fc::optional< jurisdiction_producer >();
}

void jurisdiction_base_provider::postprocess()
{
   accounts.insert( active_producer );
}

void jurisdiction_base_provider::change( const jurisdiction_basic& src )
{
   was_change = true;
   accounts.clear();
   data = src;
}

/*=============================jurisdiction_action_launcher=============================*/

void jurisdiction_action_launcher::update_provider()
{
   if( provider )
      provider->update( active_producer, producers_on_node );
}

void jurisdiction_action_launcher::init( size_t _producers_on_node )
{
   producers_on_node = _producers_on_node;
}

const account_name& jurisdiction_action_launcher::get_active_producer() const
{
   return active_producer;
}

bool jurisdiction_action_launcher::is_equal( const chainbase::database &db, const jurisdiction_producer& src )
{
   jurisdiction_producer_ordered new_src( src );

   return check_jurisdictions( db, new_src );
}

void jurisdiction_action_launcher::set_provider( ptr_provider new_provider )
{
   provider = new_provider;
}

void jurisdiction_action_launcher::update( account_name new_producer, const signature_provider_type& new_signature_provider )
{
   producer_changed = active_producer != new_producer;
   if( producer_changed )
   {
      active_producer = new_producer;
      signature_provider = new_signature_provider;
   }

   update_provider();
}

fc::optional< jurisdiction_producer > jurisdiction_action_launcher::get_jurisdiction_producer()
{
   if( provider )
      return provider->get_jurisdiction_producer();
   else
      return fc::optional< jurisdiction_producer >();
}

transaction_metadata_ptr jurisdiction_action_launcher::get_jurisdiction_transaction( const chainbase::database &db, const block_id_type& block_id, const time_point& time, const chain::chain_id_type& chain_id )
{
   if( !producer_changed || !signature_provider )
      return transaction_metadata_ptr();

   fc::optional< jurisdiction_producer > jurisdiction_data = get_jurisdiction_producer();
   if( !jurisdiction_data.valid() )
      return transaction_metadata_ptr();

   if( is_equal( db, *jurisdiction_data ) )
      return transaction_metadata_ptr();

   action on_block_update_jurisdictions_act;
   on_block_update_jurisdictions_act.account = config::system_account_name;
   on_block_update_jurisdictions_act.name = N(updateprod);
   on_block_update_jurisdictions_act.authorization = vector<permission_level>{{ active_producer, config::active_name }};
   on_block_update_jurisdictions_act.data = fc::raw::pack( *jurisdiction_data );

   signed_transaction trx;
   trx.actions.emplace_back( std::move( on_block_update_jurisdictions_act ) );

   trx.set_reference_block( block_id );

   trx.expiration = time + fc::seconds( jurisdiction_manager::artificial_transaction_timeout );
   trx.sign( signature_provider, chain_id );

   transaction_metadata_ptr res = std::make_shared< transaction_metadata >( trx );
   res->contains_jurisdiction_change = true;

   return res;
}

void jurisdiction_action_launcher::confirm()
{
   if( provider )
      provider->postprocess();
}

bool jurisdiction_action_launcher::check_jurisdictions( const chainbase::database &db, const jurisdiction_producer_ordered& src )
{
   const auto& idx = db.get_index< jurisdiction_producer_index, by_producer_jurisdiction >();
   auto itr = idx.lower_bound( std::make_tuple( src.producer, std::numeric_limits< code_jurisdiction >::min() ) );

   auto jurisdictions = src.jurisdictions;

   if( itr == idx.end() )
      return jurisdictions.empty();

   bool res = true;

   auto itr_src = jurisdictions.begin();

   while( itr != idx.end() && itr->producer == src.producer )
   {
      if( itr->jurisdiction != *itr_src )
         return false;

      ++itr;
      ++itr_src;
   }

   bool check1 = itr == idx.end() || itr->producer != src.producer;
   bool check2 = itr_src == jurisdictions.end();

   return res && check1 && check2;
}

/*=============================jurisdiction_manager=============================*/

const uint16_t jurisdiction_manager::limit_256 = 256;
const char* jurisdiction_manager::too_many_jurisdictions_exception = "Too many jurisdictions given, max value is 255.";
const int jurisdiction_manager::transaction_with_jurisdiction_timeout = 200;
const int jurisdiction_manager::artificial_transaction_timeout = 30;

bool jurisdiction_manager::check_jurisdictions( const chainbase::database &db, const jurisdiction_producer_ordered& src )
{
   return jurisdiction_action_launcher::check_jurisdictions( db, src );
}

uint16_t jurisdiction_manager::read( uint16_t idx, const std::vector< char>& buffer, std::vector< jurisdiction_basic >& dst )
{
   eosio::chain::trx_extensions ext;
   ext.set_which( idx );

   trx_extensions_visitor visitor( buffer );
   ext.visit( visitor );

   dst.emplace_back( visitor.jurisdiction );

   return visitor.jurisdiction.jurisdictions.size();
}

jurisdiction_manager::jurisdictions jurisdiction_manager::read( const extensions_type& exts )
{
   std::vector< jurisdiction_basic > res;

   uint32_t cnt = 0;

   for( const auto& item : exts )
   {
      cnt += read( item.type, item.data, res );
      FC_ASSERT( cnt < limit_256, "$(str)",("str",too_many_jurisdictions_exception) );
   }

   return res;
}

fc::variant jurisdiction_manager::get_jurisdiction( const chainbase::database& db, code_jurisdiction code )
{
   const auto& idx_by_code = db.get_index< jurisdiction_dictionary_index, by_code_jurisdiction_dictionary >();

   auto found = idx_by_code.find( code );
   if( found == idx_by_code.end() )
      return fc::variant();
   else
      return fc::mutable_variant_object()
         ("code", found->code )
         ("name", found->name.c_str() )
         ("description", found->description.c_str() );
}

bool jurisdiction_manager::update( chainbase::database& db, const jurisdiction_dictionary& info )
{
   const auto& idx_by_code = db.get_index< jurisdiction_dictionary_index, by_code_jurisdiction_dictionary >();
   const auto& idx_by_name = db.get_index< jurisdiction_dictionary_index, by_name_jurisdiction_dictionary >();

   auto _info = info;
   auto _tolower = []( const char& c ) { return std::tolower( c ); };
   std::transform( _info.name.begin(), _info.name.end(), _info.name.begin(), _tolower );

   auto found_code = idx_by_code.find( _info.code );
   FC_ASSERT( found_code == idx_by_code.end(), "jurisdiction with the same code exists" );

   auto found_name = idx_by_name.find( _info.name );
   FC_ASSERT( found_name == idx_by_name.end(), "jurisdiction with the same name exists" );

   db.create< jurisdiction_dictionary_object >( [&]( auto& obj ) {
      obj.code = _info.code;
      obj.name = _info.name.c_str();
      obj.description = _info.description.c_str();
   });

   return true;
}

bool jurisdiction_manager::update( chainbase::database& db, const jurisdiction_producer_ordered& updater )
{
   const auto& idx_by_code = db.get_index< jurisdiction_dictionary_index, by_code_jurisdiction_dictionary >();

   for( auto item : updater.jurisdictions )
      FC_ASSERT( idx_by_code.find( item ) != idx_by_code.end(), "jurisdiction doesn't exist" );

   auto& idx = db.get_mutable_index< jurisdiction_producer_index >();
   const auto& idx_by = db.get_index< jurisdiction_producer_index, by_producer_jurisdiction >();

   auto itr_state = idx_by.lower_bound( std::make_tuple( updater.producer, std::numeric_limits< code_jurisdiction >::min() ) );
   auto itr_src = updater.jurisdictions.begin();

   while( itr_src != updater.jurisdictions.end() )
   {
      if( itr_state == idx_by.end() || itr_state->producer != updater.producer )
      {
         db.create< jurisdiction_producer_object >( [&]( auto& obj ) {
            obj.producer = updater.producer;
            obj.jurisdiction = *itr_src;
         });
         ++itr_src;
      }
      else if( itr_state->jurisdiction == *itr_src )
      {
         ++itr_state;
         ++itr_src;
      }
      else
      {
         if( itr_state->jurisdiction < *itr_src )
            itr_state = idx. template erase< by_producer_jurisdiction >( itr_state );
         else
         {
            db.create< jurisdiction_producer_object >( [&]( auto& obj ) {
               obj.producer = updater.producer;
               obj.jurisdiction = *itr_src;
            });
            ++itr_src;
         }
      }
   }

   while( itr_state != idx_by.end() && itr_state->producer == updater.producer )
      itr_state = idx. template erase< by_producer_jurisdiction >( itr_state );

   return true;
}

jurisdiction_manager::match_result_type jurisdiction_manager::transaction_jurisdictions_match( const chainbase::database& db, account_name actual_producer, const packed_transaction& trx, const transaction_id_type* trx_id )
{
   bool was_already = trx_id ? ( processed_transactions.find( *trx_id ) != processed_transactions.end() ) : false;

   auto exts = trx.get_transaction().transaction_extensions;
   if( exts.empty() )
      return std::make_pair( true, was_already );

   auto deserialized_data = read( exts );

   const auto& idx_by = db.get_index< jurisdiction_producer_index, by_producer_jurisdiction >();

   for( auto item_trx_jurisdiction : deserialized_data )
   {
      for( auto item : item_trx_jurisdiction.jurisdictions )
      {
         auto found = idx_by.find( std::make_tuple( actual_producer, item ) );
         if( found != idx_by.end() )
            return std::make_pair( true, was_already );
      }
   }

   return std::make_pair( false, was_already );
}

void jurisdiction_manager::remember_transaction( const transaction_id_type& trx_id )
{
   processed_transactions.insert( trx_id );
}

void jurisdiction_manager::forget_transaction( const transaction_id_type& trx_id )
{
   processed_transactions.erase( trx_id );
}

void jurisdiction_manager::process_jurisdiction_dictionary( const chainbase::database& db, jurisdiction_dictionary_processor processor ) const
{
   const auto& idx = db.get_index< jurisdiction_dictionary_index, by_id >();

   auto lbI = idx.begin();
   auto ubI = idx.end();

   bool canContinue = true;
   for(; canContinue && lbI != ubI; ++lbI)
   {
      const jurisdiction_dictionary_object& v = *lbI;
      auto nextI = lbI;
      ++nextI;
      bool hasNext = nextI != ubI; 
      canContinue = processor(v, hasNext);
   }
}

void jurisdiction_manager::process_jurisdiction_producer( const chainbase::database& db, const account_name& lowerBound, const account_name& upperBound, jurisdiction_producer_processor processor ) const
{
   const auto& idx = db.get_index< jurisdiction_producer_index, by_producer_jurisdiction >();

   auto lbI = lowerBound.empty() ? idx.begin() : idx.lower_bound( std::make_tuple( lowerBound, std::numeric_limits<code_jurisdiction>::min() ) );
   auto ubI = upperBound.empty() ? idx.end() : idx.lower_bound( std::make_tuple( upperBound, std::numeric_limits<code_jurisdiction>::min() ) );
   
   bool canContinue = true;
   for(; canContinue && lbI != ubI; ++lbI)
   {
      const jurisdiction_producer_object& v = *lbI;
      auto nextI = lbI;
      ++nextI;
      bool hasNext = nextI != ubI; 
      canContinue = processor(v, hasNext);
   }
}

bool jurisdiction_manager::check_trx_jurisdictions_exists(const chainbase::database& db, const packed_transaction& trx)
{
   auto exts = trx.get_transaction().transaction_extensions;
   if (exts.empty())
   {
      return true;
   }

   auto deserialized_data = read(exts);
   const auto& idx = db.get_index< jurisdiction_dictionary_index, by_code_jurisdiction_dictionary >();
   for (auto item_trx_jurisdiction : deserialized_data)
   {
      for (auto item : item_trx_jurisdiction.jurisdictions)
      {
         if (idx.find(item) == idx.end())
         {
            return false;
         }
      }
   }

   return true;
}

std::string jurisdiction_manager::get_jurisdictions( const signed_transaction& trx )
{
   try
   {
      auto exts = trx.transaction_extensions;
      if( exts.empty() )
         return "";

      std::string ret;
      auto deserialized_data = read( exts );

      bool first = true;
      for( auto item : deserialized_data )
      {
         if( !first )
            ret += " : ";
         first = true;

         ret += item.to_string();
      }

      return ret;
   }
   catch( fc::exception& e )
   {
      elog( "Exception Details: ${e}", ( "e", e.to_detail_string() ) );
   }
   catch( std::exception& e )
   {
      elog( "Exception Details: ${e}", ( "e", e.what() ) );
   }
   catch( ... )
   {
      elog( "Unknown exception during when jurisdictions are read" );
   }

   return "";
}

/*=============================transaction_validator=============================*/

bool transaction_validator::check_action( const action& _action, account_name actual_producer, bool& exists )
{
   exists = _action.account == config::system_account_name && _action.name == N(updateprod);

   if( !exists )
      return false;

   jurisdiction_producer updater;

   fc::datastream<const char*> ds( _action.data.data(), _action.data.size() );
   fc::raw::unpack(ds, updater );

   return updater.producer == actual_producer;
}

void transaction_validator::clear( jurisdiction_producer_ordered& src )
{
   src.producer = account_name();
   src.jurisdictions.clear();
}

void transaction_validator::restore_old_values( bool was_data_added )
{
   new_codes = old_codes;

   if( was_data_added )
   {
      assert( !items.empty() );
      items.pop_back();
   }
}

bool transaction_validator::add( const transaction& trx )
{
   auto exts = trx.transaction_extensions;
   bool res = !exts.empty();

   if( res )
      items.push_back( jurisdiction_manager::read( exts ) );

   return res;
}

void transaction_validator::add( const action& _action )
{
   jurisdiction_producer updater;

   fc::datastream<const char*> ds( _action.data.data(), _action.data.size() );
   fc::raw::unpack(ds, updater );

   old_codes = new_codes;
   new_codes = jurisdiction_producer_ordered( updater );
}

bool transaction_validator::validate_trx( const trx_jurisdictions& trx, const jurisdiction_producer_ordered& src )
{
   for( auto& item_trx_jurisdiction : trx )
   {
      for( auto& item : item_trx_jurisdiction.jurisdictions )
      {
         auto found = src.jurisdictions.find( item );
         if( found != src.jurisdictions.end() )
            return true;
      }
   }

   return false;
}

bool transaction_validator::validate( bool was_data_added )
{
   /*
      "items.empty()"
         there isn't any transaction with jurisdiction at all 

      "items.size() == 1 && was_data_added"
         there wasn't any transaction with jurisdiction before actual
    */
   if( items.empty() || ( items.size() == 1 && was_data_added ) )
      return true;

   size_t cnt = 0;
   size_t idx_end = items.size() - 1;

   for( auto& item : items )
   {
      if( was_data_added && cnt == idx_end )
      {
         if( !validate_trx( item, old_codes ) )
            return false;
      }
      else
      {
         if( !validate_trx( item, new_codes ) )
            return false;
      }
      ++cnt;
   }

   return true;
}

transaction_validator::validate_result transaction_validator::validate_transaction( const transaction& trx, account_name actual_producer )
{
   try
   {
      validate_result result( true, false );
      bool make_validation = false;

      //Even transaction with `system_contract::updateprod` action should be checked
      bool was_data_added = add( trx );

      for( auto action : trx.actions )
      {
         if( check_action( action, actual_producer, result.second ) )
         {
            make_validation = true;
            add( action );
         }
      }

      if( make_validation )
      {
         result.first = validate( was_data_added );

         if( !result.first )
            restore_old_values( was_data_added );
      }

      return result;
   }
   catch( fc::exception& e )
   {
      elog( "Exception Details: ${e}", ( "e", e.to_detail_string() ) );
   }
   catch( std::exception& e )
   {
      elog( "Exception Details: ${e}", ( "e", e.what() ) );
   }
   catch( ... )
   {
      elog( "Unknown exception during validation of transaction" );
   }

   return validate_result( true, false );
}

void transaction_validator::clear()
{
   clear( new_codes );
   clear( old_codes );

   items.clear();
}

/*=============================transaction_comparator=============================*/

bool transaction_comparator::operator()( const transaction_metadata_ptr& a, const transaction_metadata_ptr& b ) const
{
   if( a->contains_jurisdiction_change || b->contains_jurisdiction_change )
   {
      if( a->contains_jurisdiction_change && b->contains_jurisdiction_change )
         return a->id < b->id;
      else
      {
         if( a->contains_jurisdiction_change )
            return true;
         else
            return false;
      }
   }
   else
   {
      return a->id < b->id;
   }
}

} } // eosio::chain
