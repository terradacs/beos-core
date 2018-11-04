#include "beos_privileged.hpp"

namespace eosio {

  int get_blockchain_block_number()
  {
    return tapos_block_num();
  }

}
