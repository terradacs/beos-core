/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#include <eosio/gps_plugin/gps_plugin.hpp>

namespace eosio {

static appbase::abstract_plugin& _gps_plugin = app().register_plugin<gps_plugin>();

using eosio::chain::jurisdiction_gps_provider;

class gps_plugin_impl
{
   public:

      jurisdiction_gps_provider::ptr_base gps_provider;

      producer_plugin* producer_plug = nullptr;

      gps_plugin_impl()
            : gps_provider( new jurisdiction_gps_provider() )
      {

      }
};

gps_plugin::gps_plugin()
            :my( new gps_plugin_impl() )
{
}

gps_plugin::~gps_plugin()
{
}

void gps_plugin::set_program_options(options_description& cli, options_description& cfg)
{
}

void gps_plugin::plugin_initialize(const variables_map& options)
{
  my->producer_plug = app().find_plugin<producer_plugin>();

  my->producer_plug->set_jurisdiction_provider( my->gps_provider->getptr() );
}

void gps_plugin::plugin_startup()
{
}

void gps_plugin::plugin_shutdown()
{
}

gps_apis::read_write gps_plugin::get_read_write_api()
{
  controller &c = app().find_plugin<chain_plugin>()->chain();
  return gps_apis::read_write( my->producer_plug, this, c );
}

jurisdiction_gps_provider::ptr_base gps_plugin::get_gps_provider()
{
   return my->gps_provider;
}

namespace gps_apis
{
   read_write::update_jurisdictions_results read_write::update_jurisdictions( const update_jurisdictions_params& params )
   {
      try {

         assert( producer_plug && gps_plug );

         const auto &idx_by_code = db.db().get_index<chain::jurisdiction_dictionary_index, chain::by_code_jurisdiction_dictionary>();
         for( auto item : params.jurisdictions )
         {
            FC_ASSERT( idx_by_code.find( item ) != idx_by_code.end(), "jurisdiction doesn't exist" );
         }

         gps_plug->get_gps_provider()->change( params );

         return update_jurisdictions_results( true );

      } catch (const fc::exception& e) {
         throw e;
      } catch( const std::exception& e ) {
         auto fce = fc::exception(
               FC_LOG_MESSAGE( info, "Caught std::exception: ${what}", ("what",e.what())),
               fc::std_exception_code,
               BOOST_CORE_TYPEID(e).name(),
               e.what()
         );
         throw fce;
      } catch( ... ) {
         auto fce = fc::unhandled_exception(
               FC_LOG_MESSAGE( info, "Caught unknown exception"),
               std::current_exception()
         );
         throw fce;
      }

    return update_jurisdictions_results( false );
   }
}

} // namespace eosio
