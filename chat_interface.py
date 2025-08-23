import asyncio
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import uuid

class ChatInterface:
    def __init__(self, healthcare_rag=None):
        self.healthcare_rag = healthcare_rag
        self.conversation_memory = {}
        self.healthcare_keywords = {
            "symptoms": ["pain", "fever", "headache", "nausea", "fatigue", "cough", "sore throat"],
            "conditions": ["diabetes", "hypertension", "anxiety", "depression", "asthma", "arthritis"],
            "treatments": ["medication", "therapy", "surgery", "exercise", "diet", "meditation"],
            "body_parts": ["heart", "lungs", "brain", "stomach", "liver", "kidneys", "bones"],
            "medical_terms": ["diagnosis", "prognosis", "symptoms", "treatment", "prevention", "recovery"]
        }
    
    async def process_message(self, message: str, user_id: str, conversation_id: Optional[str] = None) -> Tuple[str, List[Dict[str, str]], bool]:
        """Process a user message and return response with RAG enhancement."""
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # Get conversation context
            conversation_context = self._get_conversation_context(user_id, conversation_id)
            
            # Check if message is healthcare-related
            is_healthcare = self._is_healthcare_related(message)
            
            if is_healthcare:
                # Use RAG-enhanced response
                response, sources = await self._generate_rag_response(message, conversation_context)
            else:
                # Generate general response
                response = self._generate_general_response(message)
                sources = []
            
            # Update conversation memory
            self._update_conversation_memory(user_id, conversation_id, message, response)
            
            return response, sources, is_healthcare
            
        except Exception as e:
            print(f"⚠️ Error processing message: {e}")
            error_response = "I apologize, but I'm experiencing technical difficulties. Please try again or contact support if the issue persists."
            return error_response, [], False
    
    def _is_healthcare_related(self, message: str) -> bool:
        """Determine if a message is healthcare-related."""
        message_lower = message.lower()
        
        # Check for healthcare keywords
        for category, keywords in self.healthcare_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return True
        
        # Check for medical question patterns
        medical_patterns = [
            "what is", "how to treat", "symptoms of", "causes of",
            "treatment for", "medicine for", "doctor", "hospital",
            "pain", "sick", "illness", "disease", "condition"
        ]
        
        for pattern in medical_patterns:
            if pattern in message_lower:
                return True
        
        return False
    
    async def _generate_rag_response(self, message: str, conversation_context: str) -> Tuple[str, List[Dict[str, str]]]:
        """Generate RAG-enhanced healthcare response."""
        try:
            # Get RAG-enhanced context
            enhanced_prompt, relevant_context = self.healthcare_rag.enhance_prompt_with_rag(
                message, conversation_context
            )
            
            # Generate intelligent response based on context
            response = self._generate_intelligent_response(message, relevant_context)
            
            # Add source citations
            if relevant_context:
                response += "\n\n📚 **Sources:**\n"
                for i, ctx in enumerate(relevant_context[:3], 1):  # Show top 3 sources
                    source_name = ctx.get("source", "Unknown source")
                    response += f"{i}. {source_name}\n"
            
            # Add healthcare disclaimer
            response += self._get_healthcare_disclaimer()
            
            return response, relevant_context
            
        except Exception as e:
            print(f"⚠️ Error generating RAG response: {e}")
            return self._generate_fallback_response(message), []
    
    def _generate_intelligent_response(self, message: str, relevant_context: List[Dict[str, str]]) -> str:
        """Generate intelligent response based on RAG context."""
        message_lower = message.lower()
        
        # Analyze the type of healthcare question
        question_type = self._analyze_question_type(message)
        
        # Build response based on question type and context
        if question_type == "symptom_inquiry":
            return self._generate_symptom_response(message, relevant_context)
        elif question_type == "treatment_inquiry":
            return self._generate_treatment_response(message, relevant_context)
        elif question_type == "condition_inquiry":
            return self._generate_condition_response(message, relevant_context)
        elif question_type == "prevention_inquiry":
            return self._generate_prevention_response(message, relevant_context)
        else:
            return self._generate_general_healthcare_response(message, relevant_context)
    
    def _analyze_question_type(self, message: str) -> str:
        """Analyze the type of healthcare question."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["symptom", "sign", "feel", "experience"]):
            return "symptom_inquiry"
        elif any(word in message_lower for word in ["treat", "cure", "medicine", "therapy"]):
            return "treatment_inquiry"
        elif any(word in message_lower for word in ["what is", "condition", "disease", "disorder"]):
            return "condition_inquiry"
        elif any(word in message_lower for word in ["prevent", "avoid", "reduce risk"]):
            return "prevention_inquiry"
        else:
            return "general_inquiry"
    
    def _generate_symptom_response(self, message: str, context: List[Dict[str, str]]) -> str:
        """Generate response for symptom-related questions."""
        response = "Based on the information available, here's what I can tell you about symptoms:\n\n"
        
        # Extract relevant symptom information from context
        symptom_info = []
        for ctx in context:
            if any(word in ctx["content"].lower() for word in ["symptom", "sign", "indication"]):
                symptom_info.append(ctx["content"])
        
        if symptom_info:
            response += "**Common Symptoms:**\n"
            for info in symptom_info[:2]:  # Show top 2 relevant pieces
                response += f"• {info}\n"
        else:
            response += "**General Information:**\n"
            response += "Symptoms can vary widely depending on the condition. It's important to:\n"
            response += "• Monitor your symptoms carefully\n"
            response += "• Note when they started and how they've changed\n"
            response += "• Consider any triggers or patterns\n"
        
        response += "\n**When to Seek Medical Attention:**\n"
        response += "• Severe or persistent symptoms\n"
        response += "• Symptoms that interfere with daily activities\n"
        response += "• New or concerning symptoms\n"
        response += "• Symptoms accompanied by fever, severe pain, or other serious signs"
        
        return response
    
    def _generate_treatment_response(self, message: str, context: List[Dict[str, str]]) -> str:
        """Generate response for treatment-related questions."""
        response = "Here's information about treatment approaches:\n\n"
        
        # Extract relevant treatment information from context
        treatment_info = []
        for ctx in context:
            if any(word in ctx["content"].lower() for word in ["treatment", "therapy", "medication", "cure"]):
                treatment_info.append(ctx["content"])
        
        if treatment_info:
            response += "**Treatment Options:**\n"
            for info in treatment_info[:2]:
                response += f"• {info}\n"
        else:
            response += "**General Treatment Principles:**\n"
            response += "• Treatment plans are personalized based on individual needs\n"
            response += "• Multiple approaches may be combined for best results\n"
            response += "• Regular monitoring and adjustment may be necessary\n"
        
        response += "\n**Important Considerations:**\n"
        response += "• Always consult with healthcare professionals for personalized treatment\n"
        response += "• Follow prescribed treatment plans carefully\n"
        response += "• Report any side effects or concerns to your healthcare provider\n"
        response += "• Treatment effectiveness can vary between individuals"
        
        return response
    
    def _generate_condition_response(self, message: str, context: List[Dict[str, str]]) -> str:
        """Generate response for condition-related questions."""
        response = "Here's what I can tell you about this condition:\n\n"
        
        # Extract relevant condition information from context
        condition_info = []
        for ctx in context:
            if any(word in ctx["content"].lower() for word in ["condition", "disease", "disorder", "syndrome"]):
                condition_info.append(ctx["content"])
        
        if condition_info:
            response += "**Condition Overview:**\n"
            for info in condition_info[:2]:
                response += f"• {info}\n"
        else:
            response += "**General Information:**\n"
            response += "• Medical conditions can have various causes and presentations\n"
            response += "• Proper diagnosis requires professional medical evaluation\n"
            response += "• Early detection and treatment often improve outcomes\n"
        
        response += "\n**Key Points:**\n"
        response += "• Understanding your condition helps with management\n"
        response += "• Regular check-ups are important for monitoring\n"
        response += "• Lifestyle modifications can support treatment\n"
        response += "• Support groups and resources may be available"
        
        return response
    
    def _generate_prevention_response(self, message: str, context: List[Dict[str, str]]) -> str:
        """Generate response for prevention-related questions."""
        response = "Here are prevention strategies and recommendations:\n\n"
        
        # Extract relevant prevention information from context
        prevention_info = []
        for ctx in context:
            if any(word in ctx["content"].lower() for word in ["prevent", "avoid", "reduce risk", "lifestyle"]):
                prevention_info.append(ctx["content"])
        
        if prevention_info:
            response += "**Prevention Strategies:**\n"
            for info in prevention_info[:2]:
                response += f"• {info}\n"
        else:
            response += "**General Prevention Principles:**\n"
            response += "• Maintain a healthy lifestyle with balanced nutrition\n"
            response += "• Regular physical activity and exercise\n"
            response += "• Adequate sleep and stress management\n"
            response += "• Regular health check-ups and screenings\n"
            response += "• Avoid harmful habits like smoking and excessive alcohol"
        
        response += "\n**Lifestyle Factors:**\n"
        response += "• Healthy diet rich in fruits, vegetables, and whole grains\n"
        response += "• Regular exercise (150 minutes of moderate activity per week)\n"
        response += "• Stress reduction through meditation, yoga, or hobbies\n"
        response += "• Strong social connections and support networks"
        
        return response
    
    def _generate_general_healthcare_response(self, message: str, context: List[Dict[str, str]]) -> str:
        """Generate general healthcare response."""
        response = "I understand you have a healthcare-related question. Here's what I can share:\n\n"
        
        if context:
            response += "**Relevant Information:**\n"
            for i, ctx in enumerate(context[:2], 1):
                response += f"{i}. {ctx['content']}\n"
        
        response += "\n**General Guidance:**\n"
        response += "• Healthcare decisions should be made with professional guidance\n"
        response += "• Individual circumstances can significantly affect recommendations\n"
        response += "• Regular check-ups help maintain good health\n"
        response += "• Prevention is often more effective than treatment"
        
        return response
    
    def _generate_fallback_response(self, message: str) -> str:
        """Generate fallback response when RAG fails."""
        response = "I understand you're asking about healthcare. While I can provide general information, "
        response += "it's important to consult with qualified healthcare professionals for personalized advice.\n\n"
        
        response += "**What I can help with:**\n"
        response += "• General health information and education\n"
        response += "• Understanding common health concepts\n"
        response += "• Lifestyle and wellness recommendations\n"
        response += "• Information about preventive care\n\n"
        
        response += "**What I cannot do:**\n"
        response += "• Provide medical diagnosis\n"
        response += "• Prescribe treatments or medications\n"
        response += "• Replace professional medical advice\n"
        response += "• Handle medical emergencies"
        
        return response
    
    def _generate_general_response(self, message: str) -> str:
        """Generate response for non-healthcare messages."""
        response = "Hello! I'm your AI assistant. I'm here to help with healthcare questions and general conversation.\n\n"
        response += "**How I can help you:**\n"
        response += "• Answer healthcare and medical questions\n"
        response += "• Provide wellness and lifestyle advice\n"
        response += "• Share information about health conditions and treatments\n"
        response += "• Support general conversation and questions\n\n"
        response += "Feel free to ask me anything about health, wellness, or just chat!"
        
        return response
    
    def _get_healthcare_disclaimer(self) -> str:
        """Get standard healthcare disclaimer."""
        disclaimer = "\n\n⚠️ **IMPORTANT DISCLAIMER:**\n"
        disclaimer += "This information is for educational purposes only and should not replace professional medical advice. "
        disclaimer += "Always consult with a qualified healthcare professional for diagnosis, treatment, and medical decisions. "
        disclaimer += "If you're experiencing a medical emergency, call emergency services immediately."
        
        return disclaimer
    
    def _get_conversation_context(self, user_id: str, conversation_id: str) -> str:
        """Get conversation context for the current user and conversation."""
        if user_id not in self.conversation_memory:
            return ""
        
        if conversation_id not in self.conversation_memory[user_id]:
            return ""
        
        conversation = self.conversation_memory[user_id][conversation_id]
        if len(conversation) < 2:
            return ""
        
        # Get last few messages for context
        recent_messages = conversation[-4:]  # Last 4 messages
        context = " | ".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
        
        return context
    
    def _update_conversation_memory(self, user_id: str, conversation_id: str, user_message: str, ai_response: str):
        """Update conversation memory."""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = {}
        
        if conversation_id not in self.conversation_memory[user_id]:
            self.conversation_memory[user_id][conversation_id] = []
        
        # Add user message
        self.conversation_memory[user_id][conversation_id].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add AI response
        self.conversation_memory[user_id][conversation_id].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages to prevent memory overflow
        if len(self.conversation_memory[user_id][conversation_id]) > 20:
            self.conversation_memory[user_id][conversation_id] = self.conversation_memory[user_id][conversation_id][-20:]
    
    def get_conversation_history(self, user_id: str, conversation_id: str) -> List[Dict]:
        """Get conversation history for a specific user and conversation."""
        if user_id not in self.conversation_memory:
            return []
        
        if conversation_id not in self.conversation_memory[user_id]:
            return []
        
        return self.conversation_memory[user_id][conversation_id]
    
    def clear_conversation(self, user_id: str, conversation_id: str):
        """Clear a specific conversation."""
        if user_id in self.conversation_memory and conversation_id in self.conversation_memory[user_id]:
            del self.conversation_memory[user_id][conversation_id]
    
    def clear_user_conversations(self, user_id: str):
        """Clear all conversations for a specific user."""
        if user_id in self.conversation_memory:
            del self.conversation_memory[user_id]
    
    def generate_response(self, message: str) -> str:
        """Generate a response for the new RAG system."""
        if self._is_healthcare_related(message):
            return "I'm processing your healthcare question. Please use the RAG system for detailed medical information."
        else:
            return self._generate_general_response(message)

