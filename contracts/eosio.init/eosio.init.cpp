/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */

#include "eosio.init.hpp"

namespace eosio {

//It is possible to change any parameter at runtime.
  void init::changeparams( beos_global_state new_params )
  {
    require_auth( _self );

    checker( new_params );

    _beos_gstate = new_params;
    _beos_global.set( _beos_gstate, _self );
  }

  void init::storeparams(uint32_t )
  {
    require_auth( _self );

    auto tmp = _beos_global.exists() ? _beos_global.get() : get_beos_default_parameters();
    _beos_global.set( tmp, _self );
  }

} /// namespace eosio

EOSIO_ABI( eosio::init, (changeparams)(storeparams) )
