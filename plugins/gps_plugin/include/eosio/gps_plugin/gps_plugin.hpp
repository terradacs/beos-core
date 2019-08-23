/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#pragma once
#include <appbase/application.hpp>
#include <eosio/chain/controller.hpp>
#include <eosio/producer_plugin/producer_plugin.hpp>

namespace eosio {

  using std::unique_ptr;
  using chain::controller;

  using namespace appbase;

  using eosio::chain::jurisdiction_basic;
  using eosio::chain::jurisdiction_gps_provider;

  class gps_plugin;

namespace gps_apis
{

  class read_write
  {
    public:

      /**
       * This structure holds information if updating of jurisdictions was done.
       */
      struct update_jurisdictions_results
      {
        bool done;
        update_jurisdictions_results(bool _done ) : done(_done)
        {
        }
      };

      using update_jurisdictions_params = jurisdiction_basic;

    private:

      producer_plugin* producer_plug = nullptr;
      gps_plugin* gps_plug = nullptr;
      const controller& db;

    public:

      read_write( producer_plugin* _producer_plug, gps_plugin* _gps_plug, const controller& c)
          : producer_plug( _producer_plug ), gps_plug( _gps_plug ), db(c) {}

      update_jurisdictions_results update_jurisdictions( const update_jurisdictions_params& params );
  };

} // namespace chain_apis

class gps_plugin : public plugin<gps_plugin>
{
   public:

      APPBASE_PLUGIN_REQUIRES((producer_plugin)(chain_plugin))

      gps_plugin();
      virtual ~gps_plugin();

      virtual void set_program_options(options_description& cli, options_description& cfg) override;

      void plugin_initialize(const variables_map& options);
      void plugin_startup();
      void plugin_shutdown();

      gps_apis::read_write get_read_write_api();
      
      jurisdiction_gps_provider::ptr_base get_gps_provider();

   private:

    unique_ptr<class gps_plugin_impl> my;
};

} /// namespace eosio

FC_REFLECT( eosio::gps_apis::read_write::update_jurisdictions_results, (done) )
