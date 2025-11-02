import logging, time, json
from agents import Agent, Runner, RunResult
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, AsyncGenerator

from ..models.chat.Chat import Message
from ..agents.commander import CommanderDecision, FinalResponseInput, CallStateObserverInput, CallActionExecutorInput, CallTaskPlannerInput
from ..agents.observer import ObserverOutput
from ..agents.executor import ExecutionResult
from ..agents.planner import PlannedSteps
from ..helpers.helpers import print_detail, parse_json

_logger = logging.getLogger(__name__)


class AgentTypes(Enum):
    COMMANDER='commander'
    OBSERVER='observer'
    EXECUTOR='executor'
    PLANNER='planner'


class OODALoop():
    def __init__(self):
        self.start_time: float = None
        self.iter_number: int = 0
        self.agents = self._get_agents()
        self.iteration_log = ""
    

    def _get_agents(self) -> Dict[AgentTypes, Agent]:
        from ..server import model_set

        agents: Dict[AgentTypes, Agent] = {}
        
        from ..agents.commander import CommanderAgent
        agents[AgentTypes.COMMANDER] = CommanderAgent(
            client=model_set.main_client,
            model=model_set.main_model,
            model_settings=model_set.main_model_settings
        ).agent
        
        from ..agents.observer import ObserverAgent
        agents[AgentTypes.OBSERVER] = ObserverAgent(
            client=model_set.main_client,
            model=model_set.main_model,
            model_settings=model_set.main_model_settings
        ).agent
        
        from ..agents.executor import ExecutorAgent
        agents[AgentTypes.EXECUTOR] = ExecutorAgent(
            client=model_set.main_client,
            model=model_set.main_model,
            model_settings=model_set.main_model_settings
        ).agent
        
        from ..agents.planner import PlannerAgent
        agents[AgentTypes.PLANNER] = PlannerAgent(
            client=model_set.main_client,
            model=model_set.main_model,
            model_settings=model_set.main_model_settings
        ).agent

        return agents


    def _check_constraints(self) -> Optional[str]:
        """Check if exceeded the OODA constraints (max iterations or time)."""
        from ..server import flow_schema
        if self.iter_number >= flow_schema.loop_constrain.max_iteration:
            _logger.info("\n=== Ending OODA Loop ===")
            _logger.info(f"Reached maximum iterations ({flow_schema.loop_constrain.max_iteration})")
            return None
        
        elapsed_minutes = (time.time() - self.start_time) / 60
        if elapsed_minutes >= flow_schema.loop_constrain.max_time:
            _logger.info("\n=== Ending Research Loop ===")
            _logger.info(f"Reached maximum time ({flow_schema.loop_constrain.max_time} minutes)")
            return None
        
        return (
            f"<iteration_state>\n"
            f"<iteration_num>{self.iter_number}/{flow_schema.loop_constrain.max_iteration}</iteration_num>\n"
            f"<elapsed_time>{elapsed_minutes} min/{flow_schema.loop_constrain.max_time} min</elapsed_time>\n"
            f"</iteration_state>\n"
        )


    def _verify_observe_result(self, agent_run_result: RunResult) -> Optional[ObserverOutput]:
        try:
            return ObserverOutput.model_validate(json.loads(parse_json(agent_run_result.final_output)))
        except Exception as e:
            return None


    async def _a_observe(self, commander_decision: CommanderDecision) -> AsyncGenerator:
        from ..server import flow_schema

        input_str=(
            f"{commander_decision.action}\n"
            f"{commander_decision.tool_input.model_dump_json(indent=2)}"
        )

        observer_output: Optional[ObserverOutput] = None
        for _ in range(flow_schema.loop_constrain.per_agent_retry_max):
            observer_result = await Runner.run(
                starting_agent=self.agents[AgentTypes.OBSERVER],
                input=input_str
            )
            
            observer_output = self._verify_observe_result(observer_result)
            if not observer_output:
                continue
            else:
                self.iteration_log += (
                    f"\n"
                    f"<iteration_{self.iter_number}>\n"
                    f"<action>\n"
                    f"use tool: {commander_decision.tool_name}\n{commander_decision.action}\n"
                    f"</action>\n"
                    f"<state_observer_output>\n"
                    f"{observer_output.model_dump_json(indent=2)}\n"
                    f"</state_observer_output>\n"
                    f"</iteration_{self.iter_number}>\n"
                )
                yield (
                    f"{commander_decision.action}\n"
                    f"```json\n"
                    f"{observer_output.model_dump_json(indent=2)}\n"
                    f"```"
                )
                break
        if not observer_output:
            self.iteration_log += (
                f"\n\n"
                f"<iteration_{self.iter_number}>\n"
                f"<action>\n"
                f"use tool: {commander_decision.tool_name}\n{commander_decision.action}\n"
                f"</action>\n"
                f"<observer_output>\n"
                f"🚨 Get valid output from Observer error, maybe we should try another prompt.\n"
                f"Current prompt:\n{input_str}"
                f"</observer_output>\n"
                f"</iteration_{self.iter_number}>\n"
            )


    def _verify_execution_result(self, agent_run_result: RunResult) -> Optional[ExecutionResult]:
        try:
            return ExecutionResult.model_validate(json.loads(parse_json(agent_run_result.final_output)))
        except Exception as e:
            return None


    async def _a_execut(self, commander_decision: CommanderDecision) -> AsyncGenerator:
        from ..server import flow_schema

        input_str = (
            f"{commander_decision.action}\n"
            f"{commander_decision.tool_input.model_dump_json(indent=2)}"
        )

        execution_output: Optional[ExecutionResult] = None
        for _ in range(flow_schema.loop_constrain.per_agent_retry_max):
            execution_result = await Runner.run(
                starting_agent=self.agents[AgentTypes.EXECUTOR],
                input=input_str
            )
            
            execution_output = self._verify_execution_result(execution_result)
            if not execution_output:
                continue
            else:
                self.iteration_log += (
                    f"\n\n"
                    f"<iteration_{self.iter_number}>\n"
                    f"<action>\n"
                    f"use tool: {commander_decision.tool_name}\n{commander_decision.action}\n"
                    f"</action>\n"
                    f"<executor_result>\n"
                    f"{execution_output.model_dump_json(indent=2)}\n"
                    f"</executor_result>\n"
                    f"</iteration_{self.iter_number}>\n"
                )
                yield (
                    f"{commander_decision.action}\n"
                    f"```json\n"
                    f"{execution_output.model_dump_json(indent=2)}\n"
                    f"```"
                )
                break
        if not execution_output:
            self.iteration_log += (
                f"\n\n"
                f"<iteration_{self.iter_number}>\n"
                f"<action>\n"
                f"use tool: {commander_decision.tool_name}\n{commander_decision.action}\n"
                f"</action>\n"
                f"<executor_result>\n"
                f"🚨 Call executor error, maybe we should try another prompt.\n"
                f"Current prompt:\n{input_str}"
                f"</executor_result>\n"
                f"</iteration_{self.iter_number}>\n"
            )


    def _verify_plan_result(self, agent_run_result: RunResult) -> Optional[ExecutionResult]:
        try:
            return PlannedSteps.model_validate(json.loads(parse_json(agent_run_result.final_output)))
        except Exception as e:
            return None


    async def _a_plan(self, commander_decision: CommanderDecision) -> AsyncGenerator:
        from ..server import flow_schema

        input_str = (
            f"{commander_decision.action}\n"
            f"{commander_decision.tool_input.model_dump_json(indent=2)}"
        )

        plan_output: Optional[PlannedSteps] = None
        for _ in range(flow_schema.loop_constrain.per_agent_retry_max):
            plan_result = await Runner.run(
                starting_agent=self.agents[AgentTypes.PLANNER],
                input=input_str
            )
            
            plan_output = self._verify_plan_result(plan_result)
            if not plan_output:
                continue
            else:
                self.iteration_log += (
                    f"\n\n"
                    f"<iteration_{self.iter_number}>\n"
                    f"<action>\n"
                    f"use tool: {commander_decision.tool_name}\n{commander_decision.action}\n"
                    f"</action>\n"
                    f"<plan_result>\n"
                    f"{plan_output.model_dump_json(indent=2)}\n"
                    f"</plan_result>\n"
                    f"</iteration_{self.iter_number}>\n"
                )
                yield (
                    f"{commander_decision}\n"
                    f"```json\n"
                    f"{plan_output.model_dump_json(indent=2)}\n"
                    f"```"
                )
                break
        if not plan_output:
            self.iteration_log += (
                f"\n\n"
                f"<iteration_{self.iter_number}>\n"
                f"<action>\n"
                f"use tool: {commander_decision.tool_name}\n{commander_decision.action}\n"
                f"</action>\n"
                f"<plan_result>\n"
                f"🚨 Call planner error, maybe we should try another prompt.\n"
                f"Current prompt:\n{input_str}"
                f"</plan_result>\n"
                f"</iteration_{self.iter_number}>\n"
            )


    async def a_run(self, convo: List[Message]) -> AsyncGenerator:
        # ----- 設定初始內容 -----
        history_messages = "<history_messages>\n" + Message.to_convo_string(convo[-3:]) + "</history_messages>\n"

        self.start_time = time.time()
        self.iteration_log = ""
        while True:
            iter_state = self._check_constraints()
            if not iter_state:
                break
            
            input_str = (
                    f"# ITERATION STATE\n{iter_state}"
                    f"\n\n---\n\n"
                    f"# MESSAGES\n{history_messages}"
                    f"\n\n---\n\n"
                    f"# PREVIOUS ITERATION LOG\n{self.iteration_log}"
                    )
            print_detail(input_str, title="The input string to Commander Agent")
            # input("---stop---")

            # ----- Start from Commander agent -----
            commander_result = await Runner.run(
                starting_agent=self.agents[AgentTypes.COMMANDER],
                input=input_str
            )
            print_detail(commander_result.final_output, title="Commander Agent output")
            # input("---stop---")

            # ----- 處理 commander 判斷的結果 -----
            if not isinstance(commander_result.final_output, CommanderDecision):
                # ----- Commander agent 沒有輸出指定格式時直接yield全部內容 -----
                yield '</think>\n'
                yield commander_result.final_output
                break
            
            elif isinstance(commander_result.final_output, CommanderDecision) \
                and commander_result.final_output.tool_name == 'final_response' \
                and isinstance(commander_result.final_output.tool_input, FinalResponseInput):
                # ----- Commander agent 認為可以直接回覆用戶 -----
                yield '</think>\n'
                yield commander_result.final_output.tool_input.message_to_user
                break

            elif isinstance(commander_result.final_output, CommanderDecision) \
                and commander_result.final_output.tool_name == 'call_state_observer' \
                and isinstance(commander_result.final_output.tool_input, CallStateObserverInput):
                yield "\n\n---\n\n[Observer Agent]\n"
                async for c in self._a_observe(commander_decision=commander_result.final_output):
                    yield c

            elif isinstance(commander_result.final_output, CommanderDecision) \
                and commander_result.final_output.tool_name == 'call_action_executor' \
                and isinstance(commander_result.final_output.tool_input, CallActionExecutorInput):
                yield "\n\n---\n\n[Executor Agent]\n"
                async for c in self._a_execut(commander_decision=commander_result.final_output):
                    yield c

            elif isinstance(commander_result.final_output, CommanderDecision) \
                and commander_result.final_output.tool_name == 'call_task_planner' \
                and isinstance(commander_result.final_output.tool_input, CallTaskPlannerInput):
                yield "\n\n---\n\n[Planner Agent]\n"
                async for c in self._a_plan(commander_decision=commander_result.final_output):
                    yield c

            self.iter_number += 1