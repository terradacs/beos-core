#include <eosio/jurisdiction_history_plugin/jurisdiction_history_plugin.hpp>

namespace eosio
{
  static appbase::abstract_plugin& _jurisdiction_history_plugin = app().register_plugin<jurisdiction_history_plugin>();

  class jurisdiction_history_plugin_impl
  {
    public:
      chain_plugin *chain_plug = nullptr;
  };

  jurisdiction_history_plugin::jurisdiction_history_plugin() : my(new jurisdiction_history_plugin_impl())
  {

  }
  
  jurisdiction_history_plugin::~jurisdiction_history_plugin()
  {

  }

  void jurisdiction_history_plugin::set_program_options(options_description& cli, options_description& cfg)
  {

  }

  void jurisdiction_history_plugin::plugin_initialize(const variables_map& options)
  {
    my->chain_plug = app().find_plugin<chain_plugin>();
  }

  void jurisdiction_history_plugin::plugin_startup()
  {

  }

  void jurisdiction_history_plugin::plugin_shutdown() 
  {

  }

  jurisdiction_history_apis::read_write jurisdiction_history_plugin::get_read_write_api() const
  {
    controller& c = my->chain_plug->chain();
    return jurisdiction_history_apis::read_write(c, my->chain_plug->get_abi_serializer_max_time());
  }

  namespace jurisdiction_history_apis
  {
    get_producer_jurisdiction_for_block_results read_write::get_producer_jurisdiction_for_block(const get_producer_jurisdiction_for_block_params &params)
    {
      get_producer_jurisdiction_for_block_results result;

      return result;
    }

    get_producer_jurisdiction_history_results read_write::get_producer_jurisdiction_history(const get_producer_jurisdiction_history_results &params)
    {
      get_producer_jurisdiction_history_results result;

      return result;
    }

    void read_write::on_producer_jurisdiction_change(const chain::account_name &producer, uint64_t block_number, fc::time_point date_changed, std::vector<chain::code_jurisdiction> &new_jurisdictions)
    {
      db.db().create<jurisdiction_history_object>([&](jurisdiction_history_object &ob){
        ob.producer_name = producer;
        ob.block_number = block_number;
        ob.date_changed = date_changed;
        ob.new_jurisdictions = new_jurisdictions;
      });
    }
  } // namespace jurisdiction_history_apis


  
}