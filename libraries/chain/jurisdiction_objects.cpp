
#include <eosio/chain/jurisdiction_objects.hpp>

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

/*=============================jurisdiction_reader=============================*/

void jurisdiction_reader::read( uint16_t idx, const std::vector< char>& buffer )
{
   eosio::chain::trx_extensions ext;
   ext.set_which( idx );

   trx_extensions_visitor visitor( buffer );
   ext.visit( visitor );

   jurisdictions.emplace_back( visitor.jurisdiction );
}

bool jurisdiction_reader::read( const extensions_type& exts )
{
   try
   {
      for( const auto& item : exts )
      {
         read( std::get<0>( item ), std::get<1>( item ) );
      }
   }
   catch( ... )
   {
      return false;
   }

   return true;
}

const std::vector< trx_jurisdiction >& jurisdiction_reader::get_jurisdictions() const
{
   return jurisdictions;
}

} } // eosio::chain
