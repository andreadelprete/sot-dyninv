/*
 * Copyright 2011, Nicolas Mansard, LAAS-CNRS
 *
 * This file is part of sot-dyninv.
 * sot-dyninv is free software: you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 * sot-dyninv is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty
 * of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.  You should
 * have received a copy of the GNU Lesser General Public License along
 * with sot-dyninv.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef __sot_dyninv_commands_helper_H__
#define __sot_dyninv_commands_helper_H__

/* --- COMMON INCLUDE -------------------------------------------------- */
#include <dynamic-graph/command.h>
#include <dynamic-graph/command-direct-setter.h>
#include <dynamic-graph/command-direct-getter.h>
#include <dynamic-graph/command-bind.h>

#include <boost/function.hpp>

/* --- HELPER --------------------------------------------------------------- */
namespace dynamicgraph {
  namespace sot {
    namespace dyninv {
      using ::dynamicgraph::command::makeDirectGetter;
      using ::dynamicgraph::command::docDirectGetter;
      using ::dynamicgraph::command::makeDirectSetter;
      using ::dynamicgraph::command::docDirectSetter;
      using ::dynamicgraph::command::makeCommandVoid0;
      using ::dynamicgraph::command::docCommandVoid0;
      using ::dynamicgraph::command::makeCommandVoid1;
      using ::dynamicgraph::command::docCommandVoid1;
      using ::dynamicgraph::command::makeCommandVoid2;
      using ::dynamicgraph::command::docCommandVoid2;
      using ::dynamicgraph::command::makeCommandVerbose;
      using ::dynamicgraph::command::docCommandVerbose;
    } // namespace dyninv
  } // namespace sot
} // namespace dynamicgraph



#endif // __sot_dyninv_commands_helper_H__


