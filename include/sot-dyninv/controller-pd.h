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

#ifndef __sot_dyninv_ControllerPD_H__
#define __sot_dyninv_ControllerPD_H__
/* --------------------------------------------------------------------- */
/* --- API ------------------------------------------------------------- */
/* --------------------------------------------------------------------- */

#if defined (WIN32)
#  if defined (controller_pd_EXPORTS)
#    define SOTCONTROLLERPD_EXPORT __declspec(dllexport)
#  else
#    define SOTCONTROLLERPD_EXPORT __declspec(dllimport)
#  endif
#else
#  define SOTCONTROLLERPD_EXPORT
#endif

/* --------------------------------------------------------------------- */
/* --- INCLUDE --------------------------------------------------------- */
/* --------------------------------------------------------------------- */

/* Matrix */
#include <jrl/mal/boost.hh>
namespace ml = maal::boost;

/* SOT */
#include <dynamic-graph/entity.h>
#include <dynamic-graph/signal-ptr.h>
#include <dynamic-graph/signal-time-dependent.h>
#include <sot-core/matrix-homogeneous.h>
#include <sot-core/vector-roll-pitch-yaw.h>
#include <sot-core/matrix-rotation.h>

/* STD */
#include <string>


namespace sot {
  namespace dyninv {

    namespace dg = dynamicgraph;

  /* --------------------------------------------------------------------- */
  /* --- CLASS ----------------------------------------------------------- */
  /* --------------------------------------------------------------------- */

  class SOTCONTROLLERPD_EXPORT ControllerPD
    :public dg::Entity
    {
    public:
      static const std::string CLASS_NAME;

    public: /* --- CONSTRUCTION --- */

      ControllerPD( const std::string& name );
      virtual ~ControllerPD( void );

    public: /* --- SIGNAL --- */

      dg::SignalPtr<MatrixRotation,int> sensorWorldRotationSIN; // estimate(worldRc)
      dg::SignalPtr<MatrixHomogeneous,int> sensorEmbeddedPositionSIN; // waistRchest
      dg::SignalPtr<MatrixHomogeneous,int> contactWorldPositionSIN; // estimate(worldRf)
      dg::SignalPtr<MatrixHomogeneous,int> contactEmbeddedPositionSIN; // waistRleg
      dg::SignalTimeDependent<ml::Vector,int> anglesSOUT;  // [ flex1 flex2 yaw_drift ]
      dg::SignalTimeDependent<MatrixRotation,int> flexibilitySOUT;  // footRleg
      dg::SignalTimeDependent<MatrixRotation,int> driftSOUT;  // Ryaw = worldRc est(wRc)^-1
      dg::SignalTimeDependent<MatrixRotation,int> sensorWorldRotationSOUT;  // worldRc
      dg::SignalTimeDependent<MatrixRotation,int> waistWorldRotationSOUT;  // worldRwaist
      dg::SignalTimeDependent<MatrixHomogeneous,int> waistWorldPositionSOUT; // worldMwaist
      dg::SignalTimeDependent<ml::Vector,int> waistWorldPoseRPYSOUT; // worldMwaist

    public: /* --- FUNCTIONS --- */
      ml::Vector& computeAngles( ml::Vector& res,
				 const int& time );
      MatrixRotation& computeFlexibilityFromAngles( MatrixRotation& res,
						    const int& time );
      MatrixRotation& computeDriftFromAngles( MatrixRotation& res,
					      const int& time );
      MatrixRotation& computeSensorWorldRotation( MatrixRotation& res,
						  const int& time );
      MatrixRotation& computeWaistWorldRotation( MatrixRotation& res,
						 const int& time );
      MatrixHomogeneous& computeWaistWorldPosition( MatrixHomogeneous& res,
						    const int& time );
      ml::Vector& computeWaistWorldPoseRPY( ml::Vector& res,
					    const int& time );

    public: /* --- PARAMS --- */
      void fromSensor(const bool& inFromSensor) {    fromSensor_ = inFromSensor;  }
      bool fromSensor() const {    return fromSensor_;  }
    private:
      bool fromSensor_;
      virtual void commandLine( const std::string& cmdLine,
				std::istringstream& cmdArgs,
				std::ostream& os );
    };



  } // namespace dyninv
} // namespace sot



#endif // #ifndef __sot_dyninv_ControllerPD_H__
