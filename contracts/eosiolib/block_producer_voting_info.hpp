#pragma once

#include <stdint.h>
#include <eosiolib/serialize.hpp>

struct block_producer_voting_info
{
  uint64_t owner = 0;
  double   total_votes = 0;
  bool     is_active = false;

  EOSLIB_SERIALIZE( block_producer_voting_info, (owner)(total_votes)(is_active) )
};
