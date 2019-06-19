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
  using eosio::chain::jurisdiction_test_provider;

  class test_producer_plugin;

namespace test_producer_apis
{

  class read_write
  {
    public:

      /**
       * This structure holds length of time, which will generate shift in blockchain timeline.
       */

      struct accelerate_time_params
      {
        uint32_t time;
        std::string type;
      };

      using accelerate_mock_time_params = accelerate_time_params;
     /**
      * RPC request example:

        curl --url http://127.0.0.1:8888/v1/test_producer/accelerate_time --data
         '{
            "time":1,
            "type":"m"
          }
          '
     */

      /**
       * This structure holds number of blocks, which will be skipped.
       */

      struct accelerate_blocks_params
      {
        uint32_t blocks;
      };

     /**
      * RPC request example:

        curl --url http://127.0.0.1:8888/v1/test_producer/accelerate_blocks --data
         '{
            "blocks":1
          }
          '
     */

      struct any_results
      {
        bool done;
        any_results(bool _done ) : done(_done)
        {
        }
      };

      /**
       * This structure holds information if acceleration was done.
       */
      using accelerate_results = any_results;

      using update_jurisdictions_params = jurisdiction_basic;
      /**
       * This structure holds information if updating of jurisdictions was done.
       */
      using update_jurisdictions_results = any_results;

    private:

      producer_plugin* producer_plug = nullptr;
      test_producer_plugin* test_producer_plug = nullptr;

      template< typename CallMethod >
      accelerate_results accelerate_time_internal( const accelerate_time_params& params, CallMethod method );

    public:

      read_write( producer_plugin* _producer_plug, test_producer_plugin* _test_producer_plug )
          : producer_plug( _producer_plug ), test_producer_plug( _test_producer_plug ) {}


      accelerate_results accelerate_time( const accelerate_time_params& params );
      accelerate_results accelerate_mock_time( const accelerate_time_params& params );
      accelerate_results accelerate_blocks( const accelerate_blocks_params& params );

      update_jurisdictions_results update_jurisdictions( const update_jurisdictions_params& params );
  };

} // namespace chain_apis

class test_producer_plugin : public plugin<test_producer_plugin>
{
   public:

      APPBASE_PLUGIN_REQUIRES((test_producer_plugin))

      test_producer_plugin();
      virtual ~test_producer_plugin();

      virtual void set_program_options(options_description& cli, options_description& cfg) override;

      void plugin_initialize(const variables_map& options);
      void plugin_startup();
      void plugin_shutdown();

      test_producer_apis::read_write get_read_write_api();
      
      jurisdiction_test_provider::ptr_base get_test_provider();

   private:

    unique_ptr<class test_producer_plugin_impl> my;
};

} /// namespace eosio

FC_REFLECT( eosio::test_producer_apis::read_write::accelerate_time_params, (time)(type))
FC_REFLECT( eosio::test_producer_apis::read_write::accelerate_blocks_params, (blocks))
FC_REFLECT( eosio::test_producer_apis::read_write::accelerate_results, (done) )
