
#include <eosio/chain/jurisdiction_objects.hpp>

#include <eosio/chain/jurisdiction_object.hpp>

namespace eosio { namespace chain {

/*=============================trx_extensions_visitor=============================*/

trx_extensions_visitor::trx_extensions_visitor( const std::vector< char>& buffer )
                        : _buffer( buffer )
{
}

void trx_extensions_visitor::operator()( const trx_jurisdiction& _trx_jurisdiction ) const
{
   jurisdiction = fc::raw::unpack< trx_jurisdiction >( _buffer );
}

/*=============================jurisdiction_helper=============================*/

const uint16_t jurisdiction_helper::limit_256 = 256;
const char* jurisdiction_helper::too_many_jurisdictions_exception = "Too many jurisdictions given, max value is 255.";

bool jurisdiction_helper::check_jurisdictions( const chainbase::database &db, const jurisdiction_updater_ordered& src )
{
   const auto& idx = db.get_index< jurisdiction_index, by_producer_jurisdiction >();
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

   FC_ASSERT( itr == idx.end() || itr->producer != src.producer, "incorrect jurisdictions" );
   FC_ASSERT( itr_src == jurisdictions.end(), "incorrect jurisdictions" );

   return res;
}

uint16_t jurisdiction_helper::read( uint16_t idx, const std::vector< char>& buffer, std::vector< trx_jurisdiction >& dst )
{
   eosio::chain::trx_extensions ext;
   ext.set_which( idx );

   trx_extensions_visitor visitor( buffer );
   ext.visit( visitor );

   dst.emplace_back( visitor.jurisdiction );

   return visitor.jurisdiction.jurisdictions.size();
}

jurisdiction_helper::jurisdictions jurisdiction_helper::read( const extensions_type& exts )
{
   std::vector< trx_jurisdiction > res;

   uint32_t cnt = 0;

   for( const auto& item : exts )
   {
      cnt += read( std::get<0>( item ), std::get<1>( item ), res );
      FC_ASSERT( cnt < limit_256, "$(str)",("str",too_many_jurisdictions_exception) );
   }

   return res;
}

fc::variant jurisdiction_helper::get_jurisdiction( const chainbase::database& db, code_jurisdiction code )
{
   const auto& idx_by_code = db.get_index< jurisdiction_dictionary_index, by_code_jurisdiction_dictionary >();

   auto found = idx_by_code.find( code );
   if( found == idx_by_code.end() )
      return fc::variant();
   else
      return fc::mutable_variant_object()
         ("code", found->code )
         ("name", found->name )
         ("description", found->description );
}

bool jurisdiction_helper::update( chainbase::database& db, const info_jurisdiction& info )
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
      obj.name = _info.name;
      obj.description = _info.description;
   });

   return true;
}

bool jurisdiction_helper::update( chainbase::database& db, const jurisdiction_updater_ordered& updater )
{
   const auto& idx_by_code = db.get_index< jurisdiction_dictionary_index, by_code_jurisdiction_dictionary >();

   for( auto item : updater.jurisdictions )
      FC_ASSERT( idx_by_code.find( item ) != idx_by_code.end(), "jurisdiction doesn't exist" );

   auto& idx = db.get_mutable_index< jurisdiction_index >();
   const auto& idx_by = db.get_index< jurisdiction_index, by_producer_jurisdiction >();

   auto itr_state = idx_by.lower_bound( std::make_tuple( updater.producer, std::numeric_limits< code_jurisdiction >::min() ) );
   auto itr_src = updater.jurisdictions.begin();

   while( itr_src != updater.jurisdictions.end() )
   {
      if( itr_state == idx_by.end() || itr_state->producer != updater.producer )
      {
         db.create< jurisdiction_object >( [&]( auto& obj ) {
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
            db.create< jurisdiction_object >( [&]( auto& obj ) {
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

bool jurisdiction_helper::transaction_jurisdictions_match( const chainbase::database& db, account_name actual_producer, const packed_transaction& trx )
{
   try
   {
      auto exts = trx.get_transaction().transaction_extensions;
      if( exts.empty() )
         return true;

      auto deserialized_data = read( exts );

      const auto& idx_by = db.get_index< jurisdiction_index, by_producer_jurisdiction >();

      for( auto item_trx_jurisdiction : deserialized_data )
      {
         for( auto item : item_trx_jurisdiction.jurisdictions )
         {
            auto found = idx_by.find( std::make_tuple( actual_producer, item ) );
            if( found != idx_by.end() )
               return true;
         }
      }

      return false;
   }
   catch(...)
   {
      return false;
   }
}

} } // eosio::chain
